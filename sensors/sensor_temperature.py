# Temperature sensor simulator script.
# This is probably the most straightforward of the four sensors — temperature
# is a core metric for smart environment monitoring (HVAC control, occupancy comfort, etc.).
# We include a Unix timestamp in the payload here (unlike other sensors) because
# temperature data is particularly useful for time-series trend analysis later.

import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 Temperature Sensor started...")

# Hold readings here until we hit the dispatch interval, then send the whole batch at once
buffer = []
last_dispatch = time.time()

while True:
    # Simulate temperature around 20°C (comfortable room temperature).
    # Standard deviation of 5°C gives realistic variation throughout the day.
    value = round(20 + random.gauss(0, 5), 2)
    
    payload = {
        "sensor_type": "temperature",
        "value": value,
        "timestamp": time.time(),   # included so the fog/cloud can do time-series analysis
        "unit": "°C"
    }
    
    buffer.append(payload)
    print(f"📡 Temperature: {value}°C")

    # Once enough time has passed, send the buffered readings to the fog node
    if time.time() - last_dispatch >= DISPATCH_RATE_SEC:
        if buffer:
            try:
                response = requests.post(FOG_URL, json=buffer, timeout=5)
                print(f"✅ Dispatched batch of {len(buffer)} readings to Fog. Status: {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to send to Fog: {e}")
            
            buffer.clear()
            last_dispatch = time.time()
    
    time.sleep(FREQUENCY_SEC)