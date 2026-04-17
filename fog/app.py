from fastapi import FastAPI, Body
from processor import process_and_dispatch
import uvicorn

app = FastAPI(title="Fog Node - FEC IoT Project")

@app.post("/api/sensor")
async def receive_sensor_data(data: list = Body(...)):
    """
    Receives batch of sensor readings from sensors.
    Processes them at the fog layer and forwards to cloud.
    """
    print(f"🌫️  Fog received batch of {len(data)} readings from sensors")
    
    # Optional: print first reading for debugging
    if data:
        print(f"   First reading example: {data[0]}")
    
    processed_payload = process_and_dispatch(data)
    
    return {
        "status": "success",
        "fog_processed": True,
        "payload_forwarded_to_cloud": len(processed_payload)
    }

if __name__ == "__main__":
    print("🚀 Starting Fog Node on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)