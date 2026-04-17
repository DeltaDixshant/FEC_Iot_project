import requests
import time
from datetime import datetime

# TODO: Later we will replace this with real AWS endpoint
CLOUD_INGEST_URL = "https://5723fmkagb.execute-api.us-east-1.amazonaws.com/default/iot-ingest"

def process_and_dispatch(batch):
    if not batch:
        return []

    # 1. Validate & clean data (remove invalid readings)
    cleaned = []
    for reading in batch:
        if isinstance(reading.get("value"), (int, float)):
            cleaned.append(reading)

    if not cleaned:
        return []

    # 2. Aggregate (average value per sensor type in this batch)
    sensor_type = cleaned[0]["sensor_type"]
    values = [r["value"] for r in cleaned]
    avg_value = sum(values) / len(values)

    # 3. Simple fog processing: local threshold check (example)
    alert = None
    if sensor_type == "temperature" and avg_value > 28:
        alert = "High temperature detected!"
    elif sensor_type == "pm25" and avg_value > 35:
        alert = "Poor air quality!"

    # 4. Create reduced payload (fog does the heavy lifting)
    processed = {  # ✅ Properly indented now
        "sensor_type": sensor_type,
        "value": round(avg_value, 2),
        "unit": cleaned[0]["unit"],
        "timestamp": time.time(),
        "count": len(cleaned),
        "fog_processed": True,
        "processed_at": datetime.now().isoformat(),
        "alert": alert
    }

    print(f"✅ Fog processed {sensor_type}: {processed['value']} {processed['unit']} (from {processed['count']} readings)")

    # 5. Dispatch to AWS (real scalable backend)
    try:
        response = requests.post(CLOUD_INGEST_URL, json=processed, timeout=8)
        if response.status_code == 200:
            print(f"📤 Successfully sent to AWS SQS: {processed['sensor_type']}")
        else:
            print(f"⚠️  AWS returned {response.status_code}")
    except Exception as e:
        print(f"⚠️  Failed to send to AWS: {e}")

    return [processed]