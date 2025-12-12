# Industrial IoT Predictive Maintenance Platform
### Palantir Meritocracy Fellowship Submission

**A closed-loop Digital Twin platform for real-time asset monitoring, anomaly detection, and operational intervention.**

![Dashboard Screenshot](INSERT_YOUR_SCREENSHOT_LINK_HERE)

## 🚀 The Mission
Industrial downtime costs manufacturers $50B/year. This platform moves maintenance strategies from **Reactive** (fix it when it breaks) to **Predictive** (fix it before it breaks), using high-frequency telemetry and unsupervised learning.

## 🏗️ Architecture (The "Edge-to-Cloud" Pipeline)

| Component | Technology | Role |
|-----------|------------|------|
| **Ingestion** | **FastAPI (Python)** | High-throughput REST API receiving 100+ Hz telemetry. |
| **Storage** | **Supabase (PostgreSQL)** | Relational persistence with time-series optimization. |
| **Intelligence** | **Scikit-Learn** | **Linear Regression** for RUL (Remaining Useful Life) calculation.<br>**Isolation Forest** for unsupervised anomaly detection. |
| **Visualization** | **Streamlit** | Real-time "Operator Cockpit" with write-back capabilities. |
| **Simulation** | **Python Threading** | Multi-threaded engine simulating 3 distinct machine failure modes. |

## 🧠 Algorithmic Logic

### 1. Drift Detection (RUL)
We utilize **Linear Regression** on a rolling window of vibration data to calculate the slope of degradation.
$$y = mx + b$$
Where $m$ (slope) represents the rate of mechanical wear. The system projects when $y$ will cross the critical threshold ($115 Hz$) to estimate **Remaining Useful Life (RUL)**.

### 2. Anomaly Detection (Unsupervised)
To catch sudden shocks (non-linear failures), we employ an **Isolation Forest** algorithm.
* **Contamination Factor:** 0.05
* **Behavior:** Flags data points that deviate statistically from the local cluster, identifying "Unknown Unknowns" (e.g., impact damage or sensor spikes).

## 🛠️ How to Run

### 1. Prerequisites
* Python 3.10+
* Supabase Account

### 2. Installation
```bash
git clone [https://github.com/your-username/iot-platform.git](https://github.com/your-username/iot-platform.git)
cd iot-platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt