import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 Light Sensor started...")

buffer = []                    # Store readings until dispatch time
last_dispatch = time.time()

while True:
    # Generate realistic light reading
    value = round(300 + random.gauss(0, 100), 0)  # ~300 lux with natural variation

    payload = {
       "sensor_type": "light",
        "value": value, # lux
        "unit": "lux"
    }
    
    buffer.append(payload)
    print(f"📡 Light: {value} lux")

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