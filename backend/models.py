"""
Pydantic models for Heliotelligence API input/output validation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class LocationConfig(BaseModel):
    """Location configuration model"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude: Optional[float] = Field(0, ge=0, description="Altitude in meters")


class StringingConfig(BaseModel):
    """Array stringing configuration"""
    modules_per_string: int = Field(..., gt=0, description="Number of modules per string")
    strings_per_inverter: int = Field(..., gt=0, description="Number of strings per inverter")


class ArrayConfig(BaseModel):
    """Solar array configuration model"""
    tilt: float = Field(..., ge=0, le=90, description="Array tilt angle in degrees")
    azimuth: float = Field(..., ge=0, le=360, description="Array azimuth angle in degrees")
    stringing: StringingConfig


class ModuleParams(BaseModel):
    """Solar module parameters"""
    power: float = Field(..., gt=0, description="Module power rating in watts")
    temp_coefficient: float = Field(..., description="Temperature coefficient in %/°C")


class InverterParams(BaseModel):
    """Inverter parameters"""
    power: float = Field(..., gt=0, description="Inverter power rating in watts")
    efficiency: float = Field(..., gt=0, le=100, description="Inverter efficiency in percent")


class LossParams(BaseModel):
    """System loss parameters"""
    soiling: Optional[float] = Field(2.0, ge=0, le=100, description="Soiling losses in percent")
    shading: Optional[float] = Field(1.0, ge=0, le=100, description="Shading losses in percent")
    snow: Optional[float] = Field(0.5, ge=0, le=100, description="Snow losses in percent")
    mismatch: Optional[float] = Field(2.0, ge=0, le=100, description="Module mismatch losses in percent")
    wiring: Optional[float] = Field(2.0, ge=0, le=100, description="DC wiring losses in percent")
    connections: Optional[float] = Field(0.5, ge=0, le=100, description="Connection losses in percent")
    lid: Optional[float] = Field(1.5, ge=0, le=100, description="Light-induced degradation in percent")
    nameplate: Optional[float] = Field(1.0, ge=0, le=100, description="Nameplate rating losses in percent")
    age: Optional[float] = Field(0.0, ge=0, le=100, description="Age-related losses in percent")
    availability: Optional[float] = Field(3.0, ge=0, le=100, description="System availability losses in percent")


class PredictionRequest(BaseModel):
    """Main prediction request model"""
    location: LocationConfig
    array: ArrayConfig
    module_params: ModuleParams
    inverter_params: InverterParams
    loss_params: Optional[LossParams] = LossParams()


class LossBreakdown(BaseModel):
    """Loss breakdown response model"""
    soiling_loss_kwh: float
    shading_loss_kwh: float
    snow_loss_kwh: float
    mismatch_loss_kwh: float
    wiring_loss_kwh: float
    connections_loss_kwh: float
    lid_loss_kwh: float
    nameplate_loss_kwh: float
    age_loss_kwh: float
    availability_loss_kwh: float
    inverter_loss_kwh: float


class PredictionResponse(BaseModel):
    """Main prediction response model"""
    annual_energy_kwh: float = Field(..., description="Total annual energy production in kWh")
    performance_ratio: float = Field(..., description="System performance ratio")
    monthly_energy_kwh: List[float] = Field(..., description="Array of 12 monthly energy values in kWh")
    loss_breakdown_kwh: LossBreakdown = Field(..., description="Detailed loss breakdown in kWh")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

