import time
import math
import random
import requests
from datetime import datetime

# CONFIGURATION
API_URL = "http://localhost:8000/ingest"
SENSOR_ID = "21e70f75-718f-476f-aa66-eb8ef52b22f3"

def generate_vibration_reading(tick):
    """
    Simulates a rotating machine (like a turbine).
    - Base sine wave: The rotation.
    - Random noise: Sensor imperfection.
    - Drift: Slow increase to simulate wear/failure.
    """
    base_vibration = 100  # Baseline Hz
    
    # 1. Physics: Sine wave representing rotation
    rotation = 10 * math.sin(tick * 0.1)
    
    # 2. Reality: Random noise
    noise = random.uniform(-2, 2)
    
    # 3. Failure Mode: Slow drift upwards over time (simulating a loose bearing)
    # As 'tick' increases, the value creeps up.
    wear_tear = tick * 0.05 
    
    return base_vibration + rotation + noise + wear_tear

def simulate():
    print(f"--- Starting Simulation for Sensor {SENSOR_ID} ---")
    print("Press Ctrl+C to stop.")
    
    tick = 0
    try:
        while True:
            # Generate physics-based data
            value = generate_vibration_reading(tick)
            
            payload = {
                "sensor_id": SENSOR_ID,
                "value": round(value, 2)
            }
            
            # Send to our API
            try:
                response = requests.post(API_URL, json=payload)
                if response.status_code in [200, 201]:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent: {payload['value']} | Status: OK")
                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Connection Failed: {e}")
            
            # Wait 1 second (simulating 1Hz sample rate)
            time.sleep(1)
            tick += 1
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    simulate()