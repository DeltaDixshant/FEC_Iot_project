# PM2.5 air quality sensor simulator.
# PM2.5 refers to fine particulate matter (particles smaller than 2.5 micrometres).
# It's one of the most important air quality metrics in smart environment monitoring
# because high PM2.5 levels are linked to respiratory health issues.
# This script follows the same buffer-and-dispatch pattern as the other sensors
# so all sensors integrate cleanly with the fog node.

import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 PM2.5 Sensor started...")

# Readings sit in this buffer until it's time to dispatch the batch
buffer = []
last_dispatch = time.time()

while True:
    # Simulate a PM2.5 reading around 15 µg/m³ — roughly "Good" air quality by US EPA standards.
    # Standard deviation of 8 gives realistic variation, including occasional spikes.
    value = round(15 + random.gauss(0, 8), 2)
    
    payload = {
       "sensor_type": "pm25",
        "value": value,
        "unit": "µg/m³"
    }
    
    buffer.append(payload)
    print(f"📡 PM2.5: {value} µg/m³")

    # Flush the buffer and send to fog when the dispatch window expires
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