import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 PM2.5 Sensor started...")

buffer = []                    # Store readings until dispatch time
last_dispatch = time.time()

while True:
    # Generate realistic pm25 reading
    value = round(15 + random.gauss(0, 8), 2)   # ~15 µg/m³ with natural variation
    
    payload = {
       "sensor_type": "pm25",
        "value": value,    # µg/m³
        "unit": "µg/m³"
    }
    
    buffer.append(payload)
    print(f"📡 PM2.5: {value} µg/m³")
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