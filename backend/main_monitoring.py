"""
Heliotelligence FastAPI Backend Application
Enhanced with real-time monitoring capabilities
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from backend.models import PredictionRequest, PredictionResponse, ErrorResponse, LossBreakdown
from backend.weather import get_pvgis_tmy, validate_weather_data
from core.solar_farm_simulator import SolarFarmSimulator
from backend.monitoring import MonitoringService, SolarFarm
from backend.database import SessionLocal, engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Heliotelligence API",
    description="Physics-based solar energy yield prediction and real-time monitoring platform for the UK market",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend-backend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Mounted static files from {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")

# Additional Pydantic models for monitoring
class LocationModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude: Optional[float] = Field(0, ge=0, le=5000, description="Altitude in meters")

class StringingModel(BaseModel):
    modules_per_string: int = Field(..., ge=1, le=50, description="Number of modules per string")
    strings_per_inverter: int = Field(..., ge=1, le=100, description="Number of strings per inverter")

class ArrayModel(BaseModel):
    tilt: float = Field(..., ge=0, le=90, description="Tilt angle in degrees")
    azimuth: float = Field(..., ge=0, le=360, description="Azimuth angle in degrees")
    stringing: StringingModel

class ModuleParamsModel(BaseModel):
    power: float = Field(..., ge=100, le=1000, description="Module power rating in watts")
    temp_coefficient: float = Field(..., ge=-1, le=0, description="Temperature coefficient in %/°C")

class InverterParamsModel(BaseModel):
    power: float = Field(..., ge=1000, le=1000000, description="Inverter power rating in watts")
    efficiency: float = Field(..., ge=80, le=100, description="Inverter efficiency in %")

class LossParamsModel(BaseModel):
    soiling: Optional[float] = Field(2.0, ge=0, le=10, description="Soiling losses in %")
    shading: Optional[float] = Field(1.0, ge=0, le=20, description="Shading losses in %")
    snow: Optional[float] = Field(0.5, ge=0, le=5, description="Snow losses in %")
    mismatch: Optional[float] = Field(2.0, ge=0, le=10, description="Module mismatch losses in %")
    wiring: Optional[float] = Field(2.0, ge=0, le=10, description="DC wiring losses in %")
    connections: Optional[float] = Field(0.5, ge=0, le=5, description="Connection losses in %")
    lid: Optional[float] = Field(1.5, ge=0, le=5, description="Light-induced degradation in %")
    nameplate: Optional[float] = Field(1.0, ge=0, le=5, description="Nameplate rating losses in %")
    age: Optional[float] = Field(0.0, ge=0, le=20, description="Age-related degradation in %")
    availability: Optional[float] = Field(3.0, ge=0, le=10, description="System availability losses in %")

class RealtimeDataModel(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp of measurement")
    ac_power_kw: float = Field(..., ge=0, description="AC power output in kW")
    dc_power_kw: Optional[float] = Field(None, ge=0, description="DC power output in kW")
    irradiance_wm2: Optional[float] = Field(None, ge=0, le=2000, description="Solar irradiance in W/m²")
    ambient_temp_c: Optional[float] = Field(None, ge=-50, le=60, description="Ambient temperature in °C")
    module_temp_c: Optional[float] = Field(None, ge=-50, le=100, description="Module temperature in °C")
    wind_speed_ms: Optional[float] = Field(None, ge=0, le=50, description="Wind speed in m/s")
    inverter_efficiency: Optional[float] = Field(None, ge=0, le=100, description="Inverter efficiency in %")
    system_availability: Optional[float] = Field(100.0, ge=0, le=100, description="System availability in %")

class SolarFarmModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Solar farm name")
    location: LocationModel
    capacity_kw: float = Field(..., ge=1, le=1000000, description="Total capacity in kW")
    array: ArrayModel
    module_params: ModuleParamsModel
    inverter_params: InverterParamsModel
    loss_params: Optional[LossParamsModel] = LossParamsModel()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Heliotelligence API",
        "version": "1.0.0",
        "description": "Physics-based solar energy prediction and monitoring platform",
        "endpoints": {
            "prediction": "/api/v1/predict",
            "monitoring": "/api/v1/farms",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "heliotelligence-api",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Generate Solar Energy Prediction",
    description="Generate physics-based energy yield prediction for a solar farm configuration using UK TMY weather data"
)
async def predict_energy_yield(request: PredictionRequest):
    """
    Main prediction endpoint that generates physics-based energy yield predictions.
    
    This endpoint:
    1. Validates the input configuration
    2. Fetches TMY weather data from PVGIS for the specified UK location
    3. Runs the physics simulation using the core engine
    4. Returns detailed energy predictions and loss analysis
    """
    try:
        logger.info(f"Received prediction request for location: {request.location.latitude}, {request.location.longitude}")
        
        # Convert Pydantic models to dictionary format expected by simulator
        config = {
            'location': {
                'latitude': request.location.latitude,
                'longitude': request.location.longitude,
                'altitude': request.location.altitude or 0
            },
            'array': {
                'tilt': request.array.tilt,
                'azimuth': request.array.azimuth,
                'stringing': {
                    'modules_per_string': request.array.stringing.modules_per_string,
                    'strings_per_inverter': request.array.stringing.strings_per_inverter
                }
            },
            'module_params': {
                'power': request.module_params.power,
                'temp_coefficient': request.module_params.temp_coefficient
            },
            'inverter_params': {
                'power': request.inverter_params.power,
                'efficiency': request.inverter_params.efficiency
            },
            'loss_params': {
                'soiling': request.loss_params.soiling,
                'shading': request.loss_params.shading,
                'snow': request.loss_params.snow,
                'mismatch': request.loss_params.mismatch,
                'wiring': request.loss_params.wiring,
                'connections': request.loss_params.connections,
                'lid': request.loss_params.lid,
                'nameplate': request.loss_params.nameplate,
                'age': request.loss_params.age,
                'availability': request.loss_params.availability
            }
        }
        
        # Fetch weather data from PVGIS
        try:
            logger.info("Fetching TMY weather data from PVGIS...")
            weather_data = get_pvgis_tmy(
                latitude=request.location.latitude,
                longitude=request.location.longitude
            )
            validate_weather_data(weather_data)
            logger.info(f"Successfully fetched {len(weather_data)} hours of weather data")
            
        except Exception as e:
            logger.error(f"Weather data fetch failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch weather data: {str(e)}"
            )
        
        # Initialize and run physics simulation
        try:
            logger.info("Running physics simulation...")
            simulator = SolarFarmSimulator(config)
            results = simulator.run_simulation(weather_data)
            logger.info("Physics simulation completed successfully")
            
        except Exception as e:
            logger.error(f"Physics simulation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Physics simulation failed: {str(e)}"
            )
        
        # Convert results to response model
        try:
            loss_breakdown = LossBreakdown(**results['loss_breakdown_kwh'])
            
            response = PredictionResponse(
                annual_energy_kwh=results['annual_energy_kwh'],
                performance_ratio=results['performance_ratio'],
                monthly_energy_kwh=results['monthly_energy_kwh'],
                loss_breakdown_kwh=loss_breakdown
            )
            
            logger.info(f"Prediction completed: {results['annual_energy_kwh']:.2f} kWh annual energy")
            return response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to format response: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in prediction endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction"
        )

# Solar farm registration endpoint
@app.post("/api/v1/farms")
async def register_solar_farm(farm: SolarFarmModel, db = Depends(get_db)) -> Dict[str, Any]:
    """
    Register a new solar farm for monitoring
    """
    try:
        # Create solar farm record
        db_farm = SolarFarm(
            name=farm.name,
            location_lat=farm.location.latitude,
            location_lng=farm.location.longitude,
            location_alt=farm.location.altitude or 0,
            capacity_kw=farm.capacity_kw,
            array_tilt=farm.array.tilt,
            array_azimuth=farm.array.azimuth,
            modules_per_string=farm.array.stringing.modules_per_string,
            strings_per_inverter=farm.array.stringing.strings_per_inverter,
            module_power=farm.module_params.power,
            module_temp_coeff=farm.module_params.temp_coefficient,
            inverter_power=farm.inverter_params.power,
            inverter_efficiency=farm.inverter_params.efficiency,
            soiling_loss=farm.loss_params.soiling,
            shading_loss=farm.loss_params.shading,
            snow_loss=farm.loss_params.snow,
            mismatch_loss=farm.loss_params.mismatch,
            wiring_loss=farm.loss_params.wiring,
            connections_loss=farm.loss_params.connections,
            lid_loss=farm.loss_params.lid,
            nameplate_loss=farm.loss_params.nameplate,
            age_loss=farm.loss_params.age,
            availability_loss=farm.loss_params.availability
        )
        
        db.add(db_farm)
        db.commit()
        db.refresh(db_farm)
        
        logger.info(f"Registered solar farm: {farm.name} (ID: {db_farm.id})")
        
        return {
            "farm_id": db_farm.id,
            "name": farm.name,
            "status": "registered",
            "message": f"Solar farm '{farm.name}' registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Farm registration failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# Real-time data ingestion endpoint
@app.post("/api/v1/farms/{farm_id}/data")
async def ingest_realtime_data(farm_id: int, data: RealtimeDataModel) -> Dict[str, Any]:
    """
    Ingest real-time performance data from a solar farm
    """
    try:
        monitoring_service = MonitoringService()
        
        # Convert Pydantic model to dict
        data_dict = data.dict()
        
        # Ingest data
        success = monitoring_service.ingest_realtime_data(farm_id, data_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to ingest data")
        
        # Perform performance analysis
        analysis_result = monitoring_service.analyze_performance(farm_id)
        
        return {
            "status": "success",
            "message": "Data ingested successfully",
            "farm_id": farm_id,
            "timestamp": data.timestamp,
            "analysis": analysis_result
        }
        
    except Exception as e:
        logger.error(f"Data ingestion failed for farm {farm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Data ingestion failed: {str(e)}")

# Monitoring dashboard endpoint
@app.get("/api/v1/farms/{farm_id}/monitoring")
async def get_monitoring_dashboard(farm_id: int, hours: int = 24) -> Dict[str, Any]:
    """
    Get monitoring dashboard data for a solar farm
    """
    try:
        monitoring_service = MonitoringService()
        dashboard_data = monitoring_service.get_monitoring_data(farm_id, hours)
        
        if "error" in dashboard_data:
            raise HTTPException(status_code=404, detail=dashboard_data["error"])
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monitoring data for farm {farm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring data: {str(e)}")

# Performance analysis endpoint
@app.post("/api/v1/farms/{farm_id}/analyze")
async def analyze_performance(farm_id: int) -> Dict[str, Any]:
    """
    Trigger performance analysis for a solar farm
    """
    try:
        monitoring_service = MonitoringService()
        analysis_result = monitoring_service.analyze_performance(farm_id)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Performance analysis failed for farm {farm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

# List solar farms endpoint
@app.get("/api/v1/farms")
async def list_solar_farms(db = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    List all registered solar farms
    """
    try:
        farms = db.query(SolarFarm).filter(SolarFarm.is_active == True).all()
        
        return [
            {
                "id": farm.id,
                "name": farm.name,
                "capacity_kw": farm.capacity_kw,
                "location": {
                    "latitude": farm.location_lat,
                    "longitude": farm.location_lng
                },
                "created_at": farm.created_at.isoformat()
            }
            for farm in farms
        ]
        
    except Exception as e:
        logger.error(f"Failed to list solar farms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list farms: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": None}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Frontend route - serve index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the frontend application for all non-API routes"""
    static_dir = Path(__file__).parent.parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main_monitoring:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


