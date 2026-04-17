# This module handles everything that happens at the fog layer before data goes to AWS.
# The whole idea of our FEC (Fog-Enabled Cloud) architecture is that the fog node
# does useful work — not just a dumb relay. So here we:
#   1. Validate the incoming readings (drop anything that's clearly garbage)
#   2. Aggregate them (average) to reduce the number of records sent to the cloud
#   3. Check simple thresholds locally so we can flag alerts without round-tripping to AWS
#   4. Forward only the processed summary to the cloud via the AWS API Gateway endpoint

import requests
import time
from datetime import datetime

# This URL points to our AWS API Gateway endpoint that triggers the iot-ingest Lambda.
# Hardcoding it here for now — ideally this would live in an environment variable or config file.
CLOUD_INGEST_URL = "https://5723fmkagb.execute-api.us-east-1.amazonaws.com/default/iot-ingest"

def process_and_dispatch(batch):
    # Nothing to do if the sensor sent an empty batch — just return early
    if not batch:
        return []

    # Step 1: Validate & clean the data.
    # Sensors occasionally produce NaN or None values (e.g. if the hardware glitches),
    # so we filter those out before doing any calculations to avoid crashes downstream.
    cleaned = []
    for reading in batch:
        if isinstance(reading.get("value"), (int, float)):
            cleaned.append(reading)

    # If everything got filtered out, there's nothing useful to send
    if not cleaned:
        return []

    # Step 2: Aggregate readings from the batch.
    # Instead of sending 6 individual temperature readings (one every 5s over 30s),
    # we compute the average and send just one record. This cuts cloud storage costs
    # and keeps the DynamoDB table manageable as the system scales.
    sensor_type = cleaned[0]["sensor_type"]
    values = [r["value"] for r in cleaned]
    avg_value = sum(values) / len(values)

    # Step 3: Local threshold check — this is one of the key fog computing benefits.
    # We can trigger an alert right here on the edge without waiting for AWS to process it.
    # Thresholds are based on reasonable indoor environment standards.
    alert = None
    if sensor_type == "temperature" and avg_value > 28:
        alert = "High temperature detected!"
    elif sensor_type == "pm25" and avg_value > 35:
        # WHO guideline for PM2.5 24-hour mean is 15 µg/m³; 35 is the less strict US EPA limit
        alert = "Poor air quality!"

    # Step 4: Build the reduced payload to send to the cloud.
    # We include metadata like how many readings were aggregated (count) and the fog_processed flag
    # so the cloud side knows this data has already been cleaned and summarised.
    processed = {
        "sensor_type": sensor_type,
        "value": round(avg_value, 2),
        "unit": cleaned[0]["unit"],
        "timestamp": time.time(),
        "count": len(cleaned),          # useful for knowing how many raw readings this represents
        "fog_processed": True,
        "processed_at": datetime.now().isoformat(),
        "alert": alert
    }

    print(f"✅ Fog processed {sensor_type}: {processed['value']} {processed['unit']} (from {processed['count']} readings)")

    # Step 5: Forward the processed summary to AWS via HTTP POST.
    # We wrap it in a try/except so a network hiccup doesn't crash the whole fog node —
    # the sensor data collection will keep going even if a single dispatch fails.
    try:
        response = requests.post(CLOUD_INGEST_URL, json=processed, timeout=8)
        if response.status_code == 200:
            print(f"📤 Successfully sent to AWS SQS: {processed['sensor_type']}")
        else:
            print(f"⚠️  AWS returned {response.status_code}")
    except Exception as e:
        print(f"⚠️  Failed to send to AWS: {e}")

    return [processed]