"""
Real-time monitoring and performance analysis for Heliotelligence
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from database import Base, SessionLocal
from core.solar_farm_simulator import SolarFarmSimulator
import logging

logger = logging.getLogger(__name__)

# Database models for monitoring
class SolarFarm(Base):
    """Solar farm configuration and metadata"""
    __tablename__ = 'solar_farms'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    location_alt = Column(Float, default=0)
    capacity_kw = Column(Float, nullable=False)
    
    # System configuration (stored as JSON-like fields)
    array_tilt = Column(Float, nullable=False)
    array_azimuth = Column(Float, nullable=False)
    modules_per_string = Column(Integer, nullable=False)
    strings_per_inverter = Column(Integer, nullable=False)
    module_power = Column(Float, nullable=False)
    module_temp_coeff = Column(Float, nullable=False)
    inverter_power = Column(Float, nullable=False)
    inverter_efficiency = Column(Float, nullable=False)
    
    # System losses
    soiling_loss = Column(Float, default=2.0)
    shading_loss = Column(Float, default=1.0)
    snow_loss = Column(Float, default=0.5)
    mismatch_loss = Column(Float, default=2.0)
    wiring_loss = Column(Float, default=2.0)
    connections_loss = Column(Float, default=0.5)
    lid_loss = Column(Float, default=1.5)
    nameplate_loss = Column(Float, default=1.0)
    age_loss = Column(Float, default=0.0)
    availability_loss = Column(Float, default=3.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class RealtimeData(Base):
    """Real-time power generation data from solar farms"""
    __tablename__ = 'realtime_data'
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Power measurements
    ac_power_kw = Column(Float, nullable=False)
    dc_power_kw = Column(Float)
    
    # Environmental conditions
    irradiance_wm2 = Column(Float)
    ambient_temp_c = Column(Float)
    module_temp_c = Column(Float)
    wind_speed_ms = Column(Float)
    
    # System status
    inverter_efficiency = Column(Float)
    system_availability = Column(Float, default=100.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceAlert(Base):
    """Performance alerts and anomaly detection results"""
    __tablename__ = 'performance_alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)  # 'underperformance', 'equipment_fault', etc.
    severity = Column(String(50), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Alert details
    detected_at = Column(DateTime, nullable=False)
    expected_power_kw = Column(Float, nullable=False)
    actual_power_kw = Column(Float, nullable=False)
    performance_ratio = Column(Float, nullable=False)
    deviation_percent = Column(Float, nullable=False)
    
    # Alert message and recommendations
    message = Column(Text, nullable=False)
    recommendations = Column(Text)
    
    # Status tracking
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MonitoringService:
    """Service for real-time monitoring and performance analysis"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def ingest_realtime_data(self, farm_id: int, data: Dict[str, Any]) -> bool:
        """
        Ingest real-time data from a solar farm
        
        Args:
            farm_id: Solar farm identifier
            data: Real-time measurement data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['timestamp', 'ac_power_kw']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Parse timestamp
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = data['timestamp']
            
            # Create database record
            realtime_record = RealtimeData(
                farm_id=farm_id,
                timestamp=timestamp,
                ac_power_kw=data['ac_power_kw'],
                dc_power_kw=data.get('dc_power_kw'),
                irradiance_wm2=data.get('irradiance_wm2'),
                ambient_temp_c=data.get('ambient_temp_c'),
                module_temp_c=data.get('module_temp_c'),
                wind_speed_ms=data.get('wind_speed_ms'),
                inverter_efficiency=data.get('inverter_efficiency'),
                system_availability=data.get('system_availability', 100.0)
            )
            
            self.db.add(realtime_record)
            self.db.commit()
            
            logger.info(f"Ingested real-time data for farm {farm_id} at {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest real-time data: {e}")
            self.db.rollback()
            return False
    
    def analyze_performance(self, farm_id: int, analysis_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyze solar farm performance and detect anomalies
        
        Args:
            farm_id: Solar farm identifier
            analysis_time: Time for analysis (defaults to current time)
            
        Returns:
            Performance analysis results
        """
        if analysis_time is None:
            analysis_time = datetime.utcnow()
        
        try:
            # Get farm configuration
            farm = self.db.query(SolarFarm).filter(SolarFarm.id == farm_id).first()
            if not farm:
                raise ValueError(f"Solar farm {farm_id} not found")
            
            # Get recent real-time data (last 15 minutes)
            start_time = analysis_time - timedelta(minutes=15)
            recent_data = self.db.query(RealtimeData).filter(
                RealtimeData.farm_id == farm_id,
                RealtimeData.timestamp >= start_time,
                RealtimeData.timestamp <= analysis_time
            ).order_by(RealtimeData.timestamp.desc()).all()
            
            if not recent_data:
                logger.warning(f"No recent data found for farm {farm_id}")
                return {"status": "no_data", "message": "No recent data available"}
            
            # Get latest measurement
            latest_data = recent_data[0]
            
            # Calculate expected power using physics engine
            expected_power = self._calculate_expected_power(farm, latest_data, analysis_time)
            
            # Calculate performance metrics
            actual_power = latest_data.ac_power_kw
            performance_ratio = actual_power / expected_power if expected_power > 0 else 0
            deviation_percent = ((actual_power - expected_power) / expected_power * 100) if expected_power > 0 else 0
            
            # Determine alert level
            alert_info = self._assess_performance_deviation(deviation_percent, performance_ratio)
            
            # Create alert if necessary
            if alert_info['create_alert']:
                self._create_performance_alert(
                    farm_id=farm_id,
                    alert_type=alert_info['alert_type'],
                    severity=alert_info['severity'],
                    detected_at=analysis_time,
                    expected_power_kw=expected_power,
                    actual_power_kw=actual_power,
                    performance_ratio=performance_ratio,
                    deviation_percent=deviation_percent,
                    message=alert_info['message'],
                    recommendations=alert_info['recommendations']
                )
            
            return {
                "status": "success",
                "farm_id": farm_id,
                "analysis_time": analysis_time.isoformat(),
                "expected_power_kw": round(expected_power, 2),
                "actual_power_kw": round(actual_power, 2),
                "performance_ratio": round(performance_ratio, 3),
                "deviation_percent": round(deviation_percent, 1),
                "alert_level": alert_info['severity'],
                "message": alert_info['message']
            }
            
        except Exception as e:
            logger.error(f"Performance analysis failed for farm {farm_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_expected_power(self, farm: SolarFarm, latest_data: RealtimeData, timestamp: datetime) -> float:
        """Calculate expected power output using physics engine"""
        try:
            # Create configuration for physics engine
            config = {
                'location': {
                    'latitude': farm.location_lat,
                    'longitude': farm.location_lng,
                    'altitude': farm.location_alt
                },
                'array': {
                    'tilt': farm.array_tilt,
                    'azimuth': farm.array_azimuth,
                    'stringing': {
                        'modules_per_string': farm.modules_per_string,
                        'strings_per_inverter': farm.strings_per_inverter
                    }
                },
                'module_params': {
                    'power': farm.module_power,
                    'temp_coefficient': farm.module_temp_coeff
                },
                'inverter_params': {
                    'power': farm.inverter_power,
                    'efficiency': farm.inverter_efficiency
                },
                'loss_params': {
                    'soiling': farm.soiling_loss,
                    'shading': farm.shading_loss,
                    'snow': farm.snow_loss,
                    'mismatch': farm.mismatch_loss,
                    'wiring': farm.wiring_loss,
                    'connections': farm.connections_loss,
                    'lid': farm.lid_loss,
                    'nameplate': farm.nameplate_loss,
                    'age': farm.age_loss,
                    'availability': farm.availability_loss
                }
            }
            
            # Create weather data from measurements or use defaults
            weather_data = pd.DataFrame({
                'ghi': [latest_data.irradiance_wm2 or 500],  # Use measured or default
                'dni': [latest_data.irradiance_wm2 * 0.8 if latest_data.irradiance_wm2 else 400],
                'dhi': [latest_data.irradiance_wm2 * 0.2 if latest_data.irradiance_wm2 else 100],
                'temp_air': [latest_data.ambient_temp_c or 20],
                'wind_speed': [latest_data.wind_speed_ms or 3]
            }, index=[timestamp])
            
            # Run physics simulation for single time point
            simulator = SolarFarmSimulator(config)
            weather_data = simulator.calculate_irradiance(weather_data)
            weather_data = simulator.calculate_temperature(weather_data)
            weather_data = simulator.calculate_dc_power(weather_data)
            
            # Get instantaneous power (W to kW)
            expected_power_kw = weather_data['dc_power'].iloc[0] / 1000
            
            # Apply inverter efficiency and system availability
            expected_power_kw *= (farm.inverter_efficiency / 100)
            expected_power_kw *= (latest_data.system_availability or 100) / 100
            
            return expected_power_kw
            
        except Exception as e:
            logger.error(f"Failed to calculate expected power: {e}")
            return 0.0
    
    def _assess_performance_deviation(self, deviation_percent: float, performance_ratio: float) -> Dict[str, Any]:
        """Assess performance deviation and determine alert level"""
        
        # Define thresholds
        if deviation_percent < -20 or performance_ratio < 0.6:
            return {
                'create_alert': True,
                'alert_type': 'severe_underperformance',
                'severity': 'critical',
                'message': f'Critical underperformance detected: {deviation_percent:.1f}% below expected',
                'recommendations': 'Immediate inspection required. Check for equipment failures, shading, or soiling.'
            }
        elif deviation_percent < -10 or performance_ratio < 0.8:
            return {
                'create_alert': True,
                'alert_type': 'underperformance',
                'severity': 'high',
                'message': f'Significant underperformance detected: {deviation_percent:.1f}% below expected',
                'recommendations': 'Schedule maintenance check. Inspect for soiling, shading, or inverter issues.'
            }
        elif deviation_percent < -5 or performance_ratio < 0.9:
            return {
                'create_alert': True,
                'alert_type': 'minor_underperformance',
                'severity': 'medium',
                'message': f'Minor underperformance detected: {deviation_percent:.1f}% below expected',
                'recommendations': 'Monitor closely. Consider cleaning panels or checking system settings.'
            }
        elif deviation_percent > 10:
            return {
                'create_alert': True,
                'alert_type': 'overperformance',
                'severity': 'low',
                'message': f'Unexpected overperformance: {deviation_percent:.1f}% above expected',
                'recommendations': 'Verify measurement accuracy. Check for data quality issues.'
            }
        else:
            return {
                'create_alert': False,
                'alert_type': 'normal',
                'severity': 'normal',
                'message': f'Performance within normal range: {deviation_percent:.1f}% deviation',
                'recommendations': 'Continue normal operation.'
            }
    
    def _create_performance_alert(self, **kwargs) -> int:
        """Create a performance alert record"""
        try:
            alert = PerformanceAlert(**kwargs)
            self.db.add(alert)
            self.db.commit()
            
            logger.info(f"Created {kwargs['severity']} alert for farm {kwargs['farm_id']}: {kwargs['message']}")
            return alert.id
            
        except Exception as e:
            logger.error(f"Failed to create performance alert: {e}")
            self.db.rollback()
            return 0
    
    def get_monitoring_data(self, farm_id: int, hours: int = 24) -> Dict[str, Any]:
        """
        Get monitoring data for dashboard display
        
        Args:
            farm_id: Solar farm identifier
            hours: Number of hours of historical data to retrieve
            
        Returns:
            Monitoring dashboard data
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get farm info
            farm = self.db.query(SolarFarm).filter(SolarFarm.id == farm_id).first()
            if not farm:
                raise ValueError(f"Solar farm {farm_id} not found")
            
            # Get historical data
            historical_data = self.db.query(RealtimeData).filter(
                RealtimeData.farm_id == farm_id,
                RealtimeData.timestamp >= start_time,
                RealtimeData.timestamp <= end_time
            ).order_by(RealtimeData.timestamp).all()
            
            # Get recent alerts
            recent_alerts = self.db.query(PerformanceAlert).filter(
                PerformanceAlert.farm_id == farm_id,
                PerformanceAlert.detected_at >= start_time
            ).order_by(PerformanceAlert.detected_at.desc()).all()
            
            # Format data for frontend
            power_data = [
                {
                    'timestamp': data.timestamp.isoformat(),
                    'ac_power_kw': data.ac_power_kw,
                    'dc_power_kw': data.dc_power_kw,
                    'irradiance_wm2': data.irradiance_wm2,
                    'ambient_temp_c': data.ambient_temp_c
                }
                for data in historical_data
            ]
            
            alert_data = [
                {
                    'id': alert.id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'detected_at': alert.detected_at.isoformat(),
                    'message': alert.message,
                    'expected_power_kw': alert.expected_power_kw,
                    'actual_power_kw': alert.actual_power_kw,
                    'deviation_percent': alert.deviation_percent,
                    'is_resolved': alert.is_resolved
                }
                for alert in recent_alerts
            ]
            
            # Calculate summary statistics
            if historical_data:
                latest_data = historical_data[-1]
                avg_power = sum(d.ac_power_kw for d in historical_data) / len(historical_data)
                max_power = max(d.ac_power_kw for d in historical_data)
                
                summary = {
                    'current_power_kw': latest_data.ac_power_kw,
                    'avg_power_24h_kw': round(avg_power, 2),
                    'peak_power_24h_kw': round(max_power, 2),
                    'last_updated': latest_data.timestamp.isoformat(),
                    'total_alerts': len(alert_data),
                    'active_alerts': len([a for a in alert_data if not a['is_resolved']])
                }
            else:
                summary = {
                    'current_power_kw': 0,
                    'avg_power_24h_kw': 0,
                    'peak_power_24h_kw': 0,
                    'last_updated': None,
                    'total_alerts': 0,
                    'active_alerts': 0
                }
            
            return {
                'farm_info': {
                    'id': farm.id,
                    'name': farm.name,
                    'capacity_kw': farm.capacity_kw,
                    'location': {
                        'latitude': farm.location_lat,
                        'longitude': farm.location_lng
                    }
                },
                'summary': summary,
                'power_data': power_data,
                'alerts': alert_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring data for farm {farm_id}: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()

