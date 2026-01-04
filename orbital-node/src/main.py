import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

# Import our Physics Engine
from src.core.thermal import RadiatorSystem, ThermalThrottlingException

# Try to import AI components (graceful degradation if not available)
try:
    from src.kernel.builder import build_kernel
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False
    build_kernel = None

# Try to import semantic_kernel
try:
    from semantic_kernel.functions import KernelArguments
    SK_AVAILABLE = True
except ImportError:
    SK_AVAILABLE = False
    KernelArguments = None

app = FastAPI(
    title="Orbital Node AI Worker",
    description="Semantic Kernel worker with simulated thermal constraints."
)

# --- GLOBAL STATE (The Satellite Bus) ---
# Initialize the Physics Engine
radiator = RadiatorSystem()

# Initialize the AI Brain (Azure OpenAI)
kernel = None
summarize_function = None

if KERNEL_AVAILABLE and build_kernel:
    try:
        kernel = build_kernel()
        if kernel:
            print(">> SYSTEM: Semantic Kernel initialized successfully.")
    except Exception as e:
        print(f"!! SYSTEM WARNING: AI Kernel failed to load. {e}")
        kernel = None

# Define the AI Function (The "Job")
PROCESS_DATA_PROMPT = """
You are an AI on an orbital data center. 
Summarize the following scientific data stream concisely. 
Data: {{$input}}
"""

if kernel:
    try:
        summarize_function = kernel.create_function_from_prompt(
            function_name="Summarize",
            plugin_name="DataProcessor",
            prompt=PROCESS_DATA_PROMPT
        )
    except Exception as e:
        print(f">> WARNING: Could not create summarize function: {e}")
        summarize_function = None

class Payload(BaseModel):
    data: str
    priority: str = "NORMAL"

@app.get("/telemetry")
async def get_telemetry():
    """Returns the current thermal status of the satellite."""
    return {
        "temp_c": radiator.current_temp_c,
        "temp_k": radiator.current_temp_k,
        "status": "NOMINAL" if radiator.current_temp_k < 353.15 else "CRITICAL_HEAT",
        "cooling_capacity_watts": radiator.calculate_rejection_watts()
    }

@app.post("/process_job")
async def process_job(payload: Payload) -> Dict[str, Any]:
    """
    Accepts a compute job. 
    Refuses if the radiator is saturated (Thermal Throttling).
    """
    # 1. PHYSICS CHECK: Do we have thermal headroom?
    # We simulate the 'idle' heat load (50W) since the last request
    try:
        radiator.tick(load_watts=50.0, dt_seconds=1.0)
    except ThermalThrottlingException as e:
        # FAIL FAST: The white paper constraints say we must reject jobs if too hot.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"THERMAL THROTTLING ACTIVE: {str(e)}"
        )

    # 2. EXECUTE COMPUTE (The Heat Spike)
    start_time = time.time()
    result_text = "AI_OFFLINE_MODE"
    
    if kernel and summarize_function and SK_AVAILABLE and KernelArguments:
        try:
            # Run Semantic Kernel
            result = await kernel.invoke(
                summarize_function, 
                KernelArguments(input=payload.data)
            )
            result_text = str(result)
        except Exception as e:
            result_text = f"AI Error: {str(e)}"
    else:
        # Mock response if no API key is present (allows testing infrastructure)
        result_text = f"[MOCK KERNEL] Processed: {payload.data[:50]}..."
        
    # 3. APPLY PHYSICS CONSEQUENCES
    # Compute generates massive heat (500W). Update the Thermal Manager.
    duration = time.time() - start_time
    # Ensure minimum duration for simulation visibility
    if duration < 0.1: duration = 0.5 
    
    simulated_load_watts = 500.0 # High GPU Load
    
    # This might raise an exception if this specific job pushed us over the edge
    radiator.tick(load_watts=simulated_load_watts, dt_seconds=duration)
    
    return {
        "result": result_text,
        "telemetry": {
            "execution_time": duration,
            "final_temp_c": radiator.current_temp_c,
            "thermal_status": "NOMINAL"
        }
    }