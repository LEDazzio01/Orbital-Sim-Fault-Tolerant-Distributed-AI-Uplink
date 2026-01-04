import os
import asyncio
import httpx
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.shuttle import DataShuttleLogistics

app = FastAPI(
    title="Starcloud Ground Station",
    description="Client interface for queuing Data Shuttle payloads."
)

# Configuration: Accessing the Uplink Service (The Chaos Layer)
# We CANNOT talk to orbital-node directly.
UPLINK_HOST = os.getenv("UPLINK_HOST", "uplink-service")
UPLINK_PORT = os.getenv("UPLINK_PORT", "8001")
UPLINK_URL = f"http://{UPLINK_HOST}:{UPLINK_PORT}"

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

class TrainingJob(BaseModel):
    dataset_snippet: str
    priority: str = "NORMAL"

async def _execute_launch_protocol(payload_data: dict):
    """
    Internal task: Waits for launch window, then transmits to Uplink.
    """
    # 1. Simulate "Launch Delay" (Physical transport time)
    print(f">> GROUND STATION: Shuttle Launching in {DataShuttleLogistics.MIN_LAUNCH_DELAY_SECONDS}s...")
    await asyncio.sleep(DataShuttleLogistics.MIN_LAUNCH_DELAY_SECONDS)
    
    # 2. Transmit to Uplink (RF/Optical Link establishment)
    async with httpx.AsyncClient() as client:
        try:
            print(f">> GROUND STATION: Transmitting payload to Uplink at {UPLINK_URL}...")
            response = await client.post(
                f"{UPLINK_URL}/transmit",
                json=payload_data,
                timeout=30.0 # Long timeout for orbital link
            )
            print(f">> MISSION CONTROL: Uplink Response: {response.status_code}")
            print(f">> TELEMETRY: {response.json()}")
        except Exception as e:
            print(f"!! MISSION FAILURE: Uplink connection lost. {e}")

@app.get("/")
async def serve_dashboard():
    """Serve the Mission Control dashboard."""
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/telemetry")
async def get_telemetry():
    """Proxy telemetry from the orbital node via uplink."""
    async with httpx.AsyncClient() as client:
        try:
            # Try to get telemetry from orbital node via uplink health check
            response = await client.get(f"{UPLINK_URL}/health", timeout=5.0)
            if response.status_code == 200:
                return {
                    "temp_c": 20.0,  # Default nominal temp
                    "temp_k": 293.15,
                    "status": "NOMINAL",
                    "cooling_capacity_watts": 385.0,
                    "uplink_status": "CONNECTED"
                }
        except Exception:
            pass
    
    return {
        "temp_c": 0,
        "temp_k": 273.15,
        "status": "OFFLINE",
        "cooling_capacity_watts": 0,
        "uplink_status": "DISCONNECTED"
    }

@app.post("/upload_job")
async def upload_job(job: TrainingJob, background_tasks: BackgroundTasks):
    """
    Accepts a job from the user.
    Uses 'BackgroundTasks' to release the API client immediately while
    the 'Data Shuttle' simulation runs in the background.
    """
    # 1. Package the Data (Simulate Shuttle Manifest)
    manifest = await DataShuttleLogistics.package_payload(job.dataset_snippet)
    
    # 2. Prepare Payload for Uplink
    uplink_payload = {
        "data": job.dataset_snippet,
        "priority": job.priority
    }
    
    # 3. Schedule the Launch (Async Background Task)
    background_tasks.add_task(_execute_launch_protocol, uplink_payload)
    
    return {
        "message": "Job Accepted. Data Shuttle Manifest Created.",
        "manifest": manifest,
        "next_step": "Monitor logs for Launch and Uplink Telemetry."
    }