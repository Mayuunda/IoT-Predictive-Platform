# ... (Imports remain the same as before) ...
import time
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import numpy as np

st.set_page_config(page_title="Palantir Fleet Monitor", layout="wide")
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 1. Fetch List of Assets (The Ontology)
# We cache this so we don't hit the DB every second just for the menu
@st.cache_data
def get_assets():
    # Join logic: Get assets and their sensors
    # Note: In a real app we'd do a SQL join. Here we do 2 queries for simplicity.
    assets = supabase.table("assets").select("*").execute().data
    sensors = supabase.table("sensors").select("*").execute().data
    
    # Map them together
    asset_map = {}
    for a in assets:
        # Find the sensor for this asset
        related_sensor = next((s for s in sensors if s["asset_id"] == a["id"]), None)
        if related_sensor:
            asset_map[a["name"]] = related_sensor["id"]
            
    return asset_map

# 2. Modified Data Fetcher
def get_live_data(sensor_id):
    response = supabase.table("telemetry") \
        .select("*") \
        .eq("sensor_id", sensor_id) \
        .order("timestamp", desc=True) \
        .limit(100) \
        .execute()
    
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp') 
    return df

# Fetch maintenance history for the specific sensor
def get_maintenance_history(sensor_id):
    response = supabase.table("maintenance_tickets") \
        .select("*") \
        .eq("sensor_id", sensor_id) \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()
    return pd.DataFrame(response.data)

# --- UI LAYOUT ---
st.title("🏭 Enterprise Fleet Command")

# SIDEBAR: The Operator Controls
asset_map = get_assets()
selected_asset_name = st.sidebar.selectbox("Select Asset to Monitor", list(asset_map.keys()))
selected_sensor_id = asset_map[selected_asset_name]

st.sidebar.markdown("---")
st.sidebar.info(f"**Monitoring ID:**\n{selected_sensor_id}")
st.sidebar.markdown("Status: **ONLINE** 🟢")

# MAIN DASHBOARD (Same logic, but filtered by selected_sensor_id)
dashboard_placeholder = st.empty()
CRITICAL_THRESHOLD = 115.0 

while True:
    df = get_live_data(selected_sensor_id)
    
    with dashboard_placeholder.container():
        st.subheader(f"Live Telemetry: {selected_asset_name}")
        
        if not df.empty and len(df) > 10:
            latest_reading = df.iloc[-1]
            current_value = latest_reading['value']
            
            # --- ADVANCED ML LAYER (Regression + Anomaly Detection) ---
            
            # 1. Feature Engineering
            df['seconds_relative'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
            X = df[['seconds_relative']] # Time feature
            y = df['value']
            
            # 2. Linear Regression (Trend / RUL)
            model_reg = LinearRegression()
            model_reg.fit(X, y)
            slope = model_reg.coef_[0]
            intercept = model_reg.intercept_
            
            # 3. Isolation Forest (Anomaly Detection)
            # We look for data points that don't fit the "physics" of the last 100 points
            # Reshape data for Isolation Forest (needs 2D array)
            X_iso = df[['value']].values 
            
            # Contamination=0.05 means "we expect ~5% of data to be weird"
            iso_forest = IsolationForest(contamination=0.05, random_state=42)
            df['anomaly'] = iso_forest.fit_predict(X_iso) 
            # Returns -1 for anomaly, 1 for normal
            
            # Check if the LATEST point is an anomaly
            latest_is_anomaly = df['anomaly'].iloc[-1] == -1

            # --- DECISION LOGIC ---
            rul_message = "Stable"
            status_color = "normal" # Streamlit green
            
            # Priority 1: Is it an Anomaly? (Immediate Physics Break)
            if latest_is_anomaly:
                rul_message = "ANOMALY DETECTED (Unusual Pattern)"
                status_color = "off" # Streamlit red
            
            # Priority 2: Is it Drifting? (Long-term Wear)
            elif slope > 0.001:
                time_to_critical = (CRITICAL_THRESHOLD - intercept) / slope
                current_time_rel = df['seconds_relative'].iloc[-1]
                seconds_remaining = time_to_critical - current_time_rel
                
                if seconds_remaining > 0:
                    rul_message = f"RUL: {seconds_remaining/60:.1f} Mins"
                    if seconds_remaining < 60: status_color = "off"
                else:
                    rul_message = "CRITICAL FAILURE"
                    status_color = "off"

            # --- VISUALIZATION ---
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Vibration", f"{current_value:.2f} Hz", f"{slope:.4f}")
            with col2: st.metric("AI Status Analysis", rul_message, delta_color=status_color)
            with col3: st.metric("Buffer Size", len(df))

            # Advanced Charting
            fig = px.line(df, x='timestamp', y='value', markers=True, title=f"Live Telemetry: {selected_asset_name}")
            
            # Add Threshold
            fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash", line_color="red")
            
            # Add Trend Line
            df['trend_line'] = model_reg.predict(X)
            fig.add_scatter(x=df['timestamp'], y=df['trend_line'], mode='lines', 
                           line=dict(color='orange', dash='dot'), name='Trend Projection')
            
            # Add ANOMALY MARKERS (The Red Dots)
            anomalies = df[df['anomaly'] == -1]
            if not anomalies.empty:
                fig.add_scatter(x=anomalies['timestamp'], y=anomalies['value'], 
                               mode='markers', marker=dict(color='red', size=10, symbol='x'), 
                               name='Detected Anomaly')

            # Static key - the container handles clearing, no need for dynamic keys
            st.plotly_chart(fig, use_container_width=True, key="main_telemetry_chart")
            
            # --- CONTEXT LAYER: SYNTHESIS ---
            # Show the "Human Side" of the data
            st.markdown("### 📋 Operational Context (Recent Maintenance)")
            
            history_df = get_maintenance_history(selected_sensor_id)
            
            if not history_df.empty:
                # Clean up the timestamp for display
                history_df['created_at'] = pd.to_datetime(history_df['created_at'])
                
                # Show as a clean interactive table
                st.dataframe(
                    history_df[['created_at', 'status', 'id']],
                    column_config={
                        "created_at": st.column_config.DatetimeColumn("Dispatch Time", format="D MMM, HH:mm"),
                        "status": st.column_config.TextColumn("Ticket Status"),
                        "id": st.column_config.NumberColumn("Ticket #")
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="maintenance_history_table"
                )
            else:
                st.info("No recent maintenance history found for this asset.")

        else:
            st.warning("Initializing data stream...")
            
    time.sleep(2)  # Refresh every 2 seconds for stability