import asyncio
import random
import httpx
import os
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

app = FastAPI(
    title="Starcloud Uplink Simulator",
    description="Simulates RF/Optical link constraints: Latency, Jitter, and Packet Loss."
)

# Configuration from Docker Environment
ORBITAL_NODE_HOST = os.getenv("ORBITAL_NODE_HOST", "orbital-node")
ORBITAL_NODE_PORT = os.getenv("ORBITAL_NODE_PORT", "8002")
NODE_URL = f"http://{ORBITAL_NODE_HOST}:{ORBITAL_NODE_PORT}"

# Physics Constants
MIN_LATENCY_MS = 500   # Best case alignment 
MAX_LATENCY_MS = 2000  # Worst case alignment 
PACKET_LOSS_RATE = 0.1 # 10% failure rate [cite: 39]

class UplinkPayload(BaseModel):
    data: str
    priority: str = "NORMAL"

@app.post("/transmit")
async def transmit_packet(payload: UplinkPayload):
    """
    Simulates the transmission of a data packet to orbit.
    """
    # 1. Simulate Packet Loss (Bit Flips / LOS)
    if random.random() < PACKET_LOSS_RATE:
        print(">> UPLINK FAILURE: Packet lost in ionosphere.")
        # We return a 504 Gateway Timeout or 503 to simulate link failure
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="UPLINK ERROR: Loss of Signal (LOS)"
        )

    # 2. Simulate Latency (Speed of Light + Processing + Buffering)
    # Calculate delay in seconds
    delay = random.randint(MIN_LATENCY_MS, MAX_LATENCY_MS) / 1000.0
    print(f">> UPLINK ACTIVE: Transmitting... (ETA {delay}s)")
    await asyncio.sleep(delay)

    # 3. Forward to Orbital Node (The Proxy)
    # We use an async client to keep the proxy non-blocking
    async with httpx.AsyncClient() as client:
        try:
            # We assume the Orbital Node has an endpoint /process_job
            response = await client.post(
                f"{NODE_URL}/process_job",
                json=payload.model_dump(),
                timeout=10.0 # Strict timeout
            )
            
            # Forward the response back to Ground
            return {
                "uplink_telemetry": {
                    "latency_added_ms": delay * 1000,
                    "status": "DELIVERED"
                },
                "satellite_response": response.json()
            }
            
        except httpx.RequestError as e:
            # The satellite might be down or unreachable
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ORBITAL UNREACHABLE: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            # The satellite rejected the job (e.g., Thermal Throttling 503)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"SATELLITE ERROR: {e.response.text}"
            )

@app.get("/health")
def health_check():
    return {"status": "LINK_ESTABLISHED"}