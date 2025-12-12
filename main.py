"""
IoT Predictive Platform - FastAPI Main Application
Handles sensor telemetry ingestion and stores data in Supabase.
"""

import os
from datetime import datetime
from typing import Optional  # Still used in IngestResponse
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Environment variable validation
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing required environment variables: SUPABASE_URL and/or SUPABASE_KEY. "
        "Please create a .env file with these values."
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =============================================================================
# Pydantic Models
# =============================================================================

class TelemetryReading(BaseModel):
    sensor_id: str
    value: float
    timestamp: datetime | None = None  # Optional, defaults to now


class IngestResponse(BaseModel):
    """Response model for successful data ingestion."""
    success: bool
    message: str
    record_id: Optional[str] = None
    timestamp: datetime


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    timestamp: datetime
    supabase_connected: bool


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print("🚀 IoT Predictive Platform starting up...")
    print(f"📡 Connected to Supabase: {SUPABASE_URL[:30]}...")
    yield
    # Shutdown
    print("👋 IoT Predictive Platform shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="IoT Predictive Platform",
    description="A robust API for ingesting IoT sensor telemetry data and storing it in Supabase.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "IoT Predictive Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API and Supabase connectivity.
    """
    supabase_ok = False
    try:
        # Test Supabase connection with a simple query
        supabase.table("telemetry").select("*").limit(1).execute()
        supabase_ok = True
    except Exception:
        supabase_ok = False

    return HealthResponse(
        status="healthy" if supabase_ok else "degraded",
        timestamp=datetime.utcnow(),
        supabase_connected=supabase_ok
    )


@app.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Telemetry"],
    summary="Ingest sensor reading",
    description="Receives a sensor reading and inserts it into the telemetry table in Supabase."
)
async def ingest_sensor_reading(reading: TelemetryReading):
    """
    Ingest a sensor reading into the telemetry table.
    
    - **sensor_id**: Unique identifier for the sensor
    - **value**: The sensor reading value
    - **timestamp**: Optional timestamp (defaults to server time)
    """
    try:
        # Prepare the data for insertion
        record = {
            "sensor_id": reading.sensor_id,
            "value": reading.value,
            "timestamp": (reading.timestamp or datetime.utcnow()).isoformat(),
        }
        
        # Insert into Supabase telemetry table
        result = supabase.table("telemetry").insert(record).execute()
        
        # Check if insertion was successful
        if result.data and len(result.data) > 0:
            inserted_record = result.data[0]
            return IngestResponse(
                success=True,
                message="Sensor reading successfully ingested",
                record_id=str(inserted_record.get("id", "")),
                timestamp=datetime.utcnow()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert record: No data returned from Supabase"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest sensor reading: {str(e)}"
        )


# =============================================================================
# Run with Uvicorn (for development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

