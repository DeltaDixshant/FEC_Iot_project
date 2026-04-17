import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 Humidity Sensor started...")

buffer = []                    # Store readings until dispatch time
last_dispatch = time.time()

while True:
    # Generate realistic humidity reading
    value = round(45 + random.gauss(0, 10), 2)   # ~45% with natural variation
    
    payload = {
        "sensor_type": "humidity",
        "value": value,   # ~45%
        "unit": "%"
    }
    
    buffer.append(payload)
    print(f"📡 Humidity: {value}%")

    # Dispatch batch to Fog node at configured rate
    if time.time() - last_dispatch >= DISPATCH_RATE_SEC:
        if buffer:
            try:
                response = requests.post(FOG_URL, json=buffer, timeout=5)
                print(f"✅ Dispatched batch of {len(buffer)} readings to Fog. Status: {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to send to Fog: {e}")
            
            buffer.clear()          # reset buffer
            last_dispatch = time.time()
    
    time.sleep(FREQUENCY_SEC)