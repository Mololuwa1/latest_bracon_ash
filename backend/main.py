"""
Heliotelligence FastAPI Backend Application
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import os

# Add parent directory to path to import core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import PredictionRequest, PredictionResponse, ErrorResponse, LossBreakdown
from backend.weather import get_pvgis_tmy, validate_weather_data
from core.solar_farm_simulator import SolarFarmSimulator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Heliotelligence API",
    description="Physics-based solar energy yield prediction and monitoring platform for the UK market",
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


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Heliotelligence API",
        "version": "1.0.0",
        "description": "Physics-based solar energy prediction platform",
        "endpoints": {
            "prediction": "/api/v1/predict",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "heliotelligence-api"}


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


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

