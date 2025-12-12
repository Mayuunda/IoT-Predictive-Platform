import time
import math
import random
import requests
import threading
import os
from datetime import datetime

# CONFIGURATION
# These are your actual UUIDs from the database
SENSOR_CONFIG = [
    # Turbine-A: The one that will slowly fail (Drift)
    {"id": "9ad0f579-41e2-42f1-b4a8-6d72cae1bd7b", "name": "Turbine-A", "behavior": "failing"},
    
    # Pump-B: The healthy control group (Stable)
    {"id": "837941e5-8f07-4ad5-8d6f-58841eb226b1", "name": "Pump-B",    "behavior": "stable"},
    
    # Compressor-C: The noisy one (Spikes/Anomalies)
    {"id": "ce99ac44-6e2e-40af-8ac1-441deda9b0b5", "name": "Compressor-C", "behavior": "erratic"},
]

# Defaults to localhost if not set, but allows Docker to override it
API_URL = os.getenv("API_URL", "http://localhost:8000/ingest")

def simulate_sensor(sensor):
    """
    Runs a simulation loop for a SINGLE sensor.
    """
    tick = 0
    sensor_id = sensor["id"]
    behavior = sensor["behavior"]
    print(f"Starting simulation for {sensor['name']} ({behavior})")
    
    while True:
        base_vibration = 100
        noise = random.uniform(-2, 2)
        value = 0
        
        # Behavior Logic
        if behavior == "failing":
            # Linear drift upwards (The one that will explode)
            drift = tick * 0.08
            value = base_vibration + (10 * math.sin(tick * 0.1)) + noise + drift
        
        elif behavior == "stable":
            # Just vibration, no drift
            value = base_vibration + (5 * math.sin(tick * 0.2)) + noise
            
        elif behavior == "erratic":
            # Random spikes every now and then
            spike = 20 if random.random() > 0.95 else 0
            value = base_vibration + noise + spike

        # Payload
        payload = {
            "sensor_id": sensor_id,
            "value": round(value, 2)
        }
        
        try:
            # Send to API
            requests.post(API_URL, json=payload)
        except Exception as e:
            # Simple error logging
            print(f"[{sensor['name']}] Connection Error: {e}")
            
        time.sleep(1) # 1Hz frequency
        tick += 1

# Main Execution: Spin up threads
if __name__ == "__main__":
    print("--- 🏭 STARTING FLEET SIMULATION ---")
    print(f"Targeting API: {API_URL}")
    print("Press Ctrl+C to stop all machines.")
    
    threads = []
    
    for sensor in SENSOR_CONFIG:
        # Create a thread for each machine
        t = threading.Thread(target=simulate_sensor, args=(sensor,))
        t.daemon = True # Kills thread when main program exits
        t.start()
        threads.append(t)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Fleet...")