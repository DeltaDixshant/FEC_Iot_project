# This is the entry point for the fog node in our FEC IoT architecture.
# The fog node sits between the sensors and the cloud (AWS), which is the whole
# point of fog computing — we don't want raw sensor data flooding directly into
# the cloud every few seconds. Instead, we collect, validate, and aggregate it here first.
# Using FastAPI because it's lightweight and async, which is perfect for handling
# multiple sensor streams at the same time without blocking.

from fastapi import FastAPI, Body
from processor import process_and_dispatch
import uvicorn

# Give the API a meaningful title so it's easier to identify in the docs/logs
app = FastAPI(title="Fog Node - FEC IoT Project")

@app.post("/api/sensor")
async def receive_sensor_data(data: list = Body(...)):
    """
    This endpoint is what all the sensor scripts call to send their batched readings.
    We accept a list because sensors buffer multiple readings before dispatching —
    sending them in a batch is way more efficient than one HTTP request per reading.
    The actual processing logic (aggregation, threshold checks, AWS forwarding) is
    all handled in processor.py to keep this file clean and focused on routing.
    """
    print(f"🌫️  Fog received batch of {len(data)} readings from sensors")
    
    # Print the first reading so we can sanity-check the data format during development
    if data:
        print(f"   First reading example: {data[0]}")
    
    # Hand off to the processor — it does the heavy lifting
    processed_payload = process_and_dispatch(data)
    
    # Return a simple status response so the sensor scripts know the batch was received
    return {
        "status": "success",
        "fog_processed": True,
        "payload_forwarded_to_cloud": len(processed_payload)
    }

if __name__ == "__main__":
    # Run on localhost so only local sensor scripts (running on the same machine/VM) can reach it
    print("🚀 Starting Fog Node on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)