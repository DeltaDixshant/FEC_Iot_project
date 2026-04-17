# Light sensor simulator script.
# Simulates a lux (illuminance) sensor — the kind you'd find in a smart building
# system to control blinds or lighting automatically based on ambient light levels.
# Like the other sensor scripts, this runs continuously as its own process,
# buffers readings, and dispatches them in batches to the fog node.

import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 Light Sensor started...")

# Buffer collects readings between dispatch intervals
buffer = []
last_dispatch = time.time()

while True:
    # Simulate an indoor light level around 300 lux (typical office lighting).
    # Using gauss() with a standard deviation of 100 gives a realistic spread — lights flicker,
    # clouds pass by windows, etc. round(..., 0) keeps it as a whole number like a real sensor.
    value = round(300 + random.gauss(0, 100), 0)

    payload = {
       "sensor_type": "light",
        "value": value,
        "unit": "lux"
    }
    
    buffer.append(payload)
    print(f"📡 Light: {value} lux")

    # Dispatch the accumulated batch to the fog node once the interval is reached
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