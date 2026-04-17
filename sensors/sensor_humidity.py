# Humidity sensor simulator script.
# In a real deployment this would read from actual hardware (e.g. a DHT22 sensor over GPIO).
# For this project we simulate realistic sensor data using Gaussian (normal) distribution
# noise, which is closer to real sensor behaviour than just using random.uniform().
# The script runs as a standalone process alongside the other sensor scripts.

import requests
import time
import random
import json
from config import FREQUENCY_SEC, DISPATCH_RATE_SEC, FOG_URL

print("🚀 Humidity Sensor started...")

# We use a buffer instead of sending every single reading immediately.
# This way we accumulate readings for DISPATCH_RATE_SEC seconds and then
# send them all in one HTTP request to the fog node — much more efficient.
buffer = []
last_dispatch = time.time()

while True:
    # Simulate a humidity reading centred around 45% RH with some natural variation.
    # gauss(0, 10) gives us a bell-curve spread of ±10% which looks realistic.
    value = round(45 + random.gauss(0, 10), 2)
    
    payload = {
        "sensor_type": "humidity",
        "value": value,
        "unit": "%"
    }
    
    buffer.append(payload)
    print(f"📡 Humidity: {value}%")

    # Check if it's time to flush the buffer and dispatch to the fog node.
    # We compare elapsed time against DISPATCH_RATE_SEC so the interval stays
    # accurate even if individual sleep() calls drift slightly.
    if time.time() - last_dispatch >= DISPATCH_RATE_SEC:
        if buffer:
            try:
                response = requests.post(FOG_URL, json=buffer, timeout=5)
                print(f"✅ Dispatched batch of {len(buffer)} readings to Fog. Status: {response.status_code}")
            except Exception as e:
                # Network errors are expected during development — log and move on
                print(f"❌ Failed to send to Fog: {e}")
            
            # Clear the buffer and reset the timer regardless of success/failure
            buffer.clear()
            last_dispatch = time.time()
    
    # Wait until it's time to take the next reading
    time.sleep(FREQUENCY_SEC)