import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Define our Fleet
fleet_data = [
    {"name": "Turbine-A (Main)", "type": "Gas Turbine", "location": "Sector 1"},
    {"name": "Pump-B (Auxiliary)", "type": "Hydraulic Pump", "location": "Sector 2"},
    {"name": "Compressor-C", "type": "Air Compressor", "location": "Sector 1"},
]

print("--- Seeding Fleet Data ---")

for machine in fleet_data:
    # 1. Create Asset
    asset_res = supabase.table("assets").insert(machine).execute()
    asset_id = asset_res.data[0]['id']
    print(f"Created Asset: {machine['name']} ({asset_id})")
    
    # 2. Attach a Sensor to it
    sensor_data = {
        "asset_id": asset_id,
        "type": "vibration",
        "unit": "hertz"
    }
    sensor_res = supabase.table("sensors").insert(sensor_data).execute()
    sensor_id = sensor_res.data[0]['id']
    print(f" -> Attached Sensor: {sensor_id}")

print("--- Fleet Ready ---")