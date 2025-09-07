"""
Solar Farm Simulator - Physics Core Engine for Heliotelligence
"""

import pandas as pd
import numpy as np
import pvlib
from typing import Dict, Any
import json


class SolarFarmSimulator:
    """
    Core physics simulation engine for solar farm energy yield predictions.
    Uses pvlib for all solar physics calculations and pandas for time-series data handling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simulator with configuration dictionary.
        
        Args:
            config: Dictionary containing nested objects for:
                - location: {latitude, longitude, altitude}
                - array: {tilt, azimuth, stringing}
                - module_params: {power, temp_coefficient}
                - inverter_params: {power, efficiency}
                - loss_params: {soiling, shading, etc.}
        """
        self.config = config
        self.location = config['location']
        self.array = config['array']
        self.module_params = config['module_params']
        self.inverter_params = config['inverter_params']
        self.loss_params = config['loss_params']
        
        # Create pvlib Location object
        self.site = pvlib.location.Location(
            latitude=self.location['latitude'],
            longitude=self.location['longitude'],
            altitude=self.location.get('altitude', 0),
            tz='Europe/London'
        )
        
    def calculate_irradiance(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate plane-of-array irradiance from weather data.
        
        Args:
            weather_data: DataFrame with columns ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
            
        Returns:
            DataFrame with additional irradiance columns
        """
        # Calculate solar position
        solar_position = self.site.get_solarposition(weather_data.index)
        
        # Calculate plane-of-array irradiance
        poa_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.array['tilt'],
            surface_azimuth=self.array['azimuth'],
            dni=weather_data['dni'],
            ghi=weather_data['ghi'],
            dhi=weather_data['dhi'],
            solar_zenith=solar_position['apparent_zenith'],
            solar_azimuth=solar_position['azimuth']
        )
        
        # Add irradiance data to weather DataFrame
        weather_data = weather_data.copy()
        weather_data['poa_global'] = poa_irradiance['poa_global']
        weather_data['poa_direct'] = poa_irradiance['poa_direct']
        weather_data['poa_diffuse'] = poa_irradiance['poa_diffuse']
        
        return weather_data
    
    def calculate_temperature(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cell temperature from weather conditions.
        
        Args:
            weather_data: DataFrame with irradiance and weather data
            
        Returns:
            DataFrame with cell temperature column added
        """
        # Use Sandia cell temperature model
        cell_temp = pvlib.temperature.sapm_cell(
            poa_global=weather_data['poa_global'],
            temp_air=weather_data['temp_air'],
            wind_speed=weather_data['wind_speed'],
            a=-3.47,  # Default SAPM parameters for open rack
            b=-0.0594,
            deltaT=3
        )
        
        weather_data = weather_data.copy()
        weather_data['cell_temperature'] = cell_temp
        
        return weather_data
    
    def calculate_dc_power(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate DC power output from irradiance and temperature.
        
        Args:
            weather_data: DataFrame with irradiance and temperature data
            
        Returns:
            DataFrame with DC power column added
        """
        # Use single diode model for DC power calculation
        # Create module parameters for pvlib
        module_params = {
            'pdc0': self.module_params['power'],  # Power at STC (W)
            'gamma_pdc': self.module_params['temp_coefficient'],  # Temperature coefficient (%/°C)
        }
        
        # Calculate DC power using simple temperature-corrected model
        # P = P_stc * (G/G_stc) * (1 + gamma * (T_cell - T_stc))
        G_stc = 1000  # Standard test conditions irradiance (W/m²)
        T_stc = 25    # Standard test conditions temperature (°C)
        
        dc_power = (
            module_params['pdc0'] * 
            (weather_data['poa_global'] / G_stc) * 
            (1 + module_params['gamma_pdc'] / 100 * (weather_data['cell_temperature'] - T_stc))
        )
        
        # Ensure no negative power
        dc_power = np.maximum(dc_power, 0)
        
        weather_data = weather_data.copy()
        weather_data['dc_power'] = dc_power
        
        return weather_data
    
    def calculate_losses(self, weather_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate various system losses.
        
        Args:
            weather_data: DataFrame with DC power data
            
        Returns:
            Dictionary with loss breakdown in kWh
        """
        # Calculate annual energy without losses
        dc_energy_ideal = weather_data['dc_power'].sum() / 1000  # Convert W to kWh
        
        # Apply losses from configuration
        soiling_loss = dc_energy_ideal * (self.loss_params.get('soiling', 0) / 100)
        shading_loss = dc_energy_ideal * (self.loss_params.get('shading', 0) / 100)
        snow_loss = dc_energy_ideal * (self.loss_params.get('snow', 0) / 100)
        mismatch_loss = dc_energy_ideal * (self.loss_params.get('mismatch', 0) / 100)
        wiring_loss = dc_energy_ideal * (self.loss_params.get('wiring', 0) / 100)
        connections_loss = dc_energy_ideal * (self.loss_params.get('connections', 0) / 100)
        lid_loss = dc_energy_ideal * (self.loss_params.get('lid', 0) / 100)
        nameplate_loss = dc_energy_ideal * (self.loss_params.get('nameplate', 0) / 100)
        age_loss = dc_energy_ideal * (self.loss_params.get('age', 0) / 100)
        availability_loss = dc_energy_ideal * (self.loss_params.get('availability', 0) / 100)
        
        # Inverter losses
        inverter_efficiency = self.inverter_params.get('efficiency', 95) / 100
        inverter_loss = dc_energy_ideal * (1 - inverter_efficiency)
        
        loss_breakdown = {
            'soiling_loss_kwh': soiling_loss,
            'shading_loss_kwh': shading_loss,
            'snow_loss_kwh': snow_loss,
            'mismatch_loss_kwh': mismatch_loss,
            'wiring_loss_kwh': wiring_loss,
            'connections_loss_kwh': connections_loss,
            'lid_loss_kwh': lid_loss,
            'nameplate_loss_kwh': nameplate_loss,
            'age_loss_kwh': age_loss,
            'availability_loss_kwh': availability_loss,
            'inverter_loss_kwh': inverter_loss
        }
        
        return loss_breakdown
    
    def run_simulation(self, weather_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main simulation method that orchestrates all physics calculations.
        
        Args:
            weather_data: DataFrame with TMY weather data
            
        Returns:
            JSON object with key metrics:
            - annual_energy_kwh: Total annual energy production
            - performance_ratio: System performance ratio
            - monthly_energy_kwh: Array of 12 monthly energy values
            - loss_breakdown_kwh: Dictionary of detailed losses
        """
        # Step 1: Calculate irradiance
        weather_data = self.calculate_irradiance(weather_data)
        
        # Step 2: Calculate temperature
        weather_data = self.calculate_temperature(weather_data)
        
        # Step 3: Calculate DC power
        weather_data = self.calculate_dc_power(weather_data)
        
        # Step 4: Calculate losses
        loss_breakdown = self.calculate_losses(weather_data)
        
        # Calculate final AC energy after all losses
        dc_energy_ideal = weather_data['dc_power'].sum() / 1000  # Convert W to kWh
        total_losses = sum(loss_breakdown.values())
        annual_energy_kwh = dc_energy_ideal - total_losses
        
        # Calculate monthly energy breakdown
        weather_data['month'] = weather_data.index.month
        monthly_dc = weather_data.groupby('month')['dc_power'].sum() / 1000  # Convert to kWh
        
        # Apply proportional losses to monthly values
        loss_factor = annual_energy_kwh / dc_energy_ideal if dc_energy_ideal > 0 else 0
        monthly_energy_kwh = (monthly_dc * loss_factor).tolist()
        
        # Ensure we have 12 months (fill missing months with 0)
        monthly_energy_complete = [0] * 12
        for month in range(1, 13):
            if month in monthly_dc.index:
                monthly_energy_complete[month-1] = monthly_dc[month] * loss_factor
        
        # Calculate performance ratio
        # PR = Actual Energy / (Irradiation * System Power * Standard Irradiance)
        total_irradiation = weather_data['poa_global'].sum() / 1000  # Convert Wh/m² to kWh/m²
        system_power_kw = self.module_params['power'] / 1000  # Convert W to kW
        standard_irradiance = 1.0  # kW/m²
        
        theoretical_energy = total_irradiation * system_power_kw / standard_irradiance
        performance_ratio = annual_energy_kwh / theoretical_energy if theoretical_energy > 0 else 0
        
        # Return results as specified JSON structure
        results = {
            'annual_energy_kwh': round(annual_energy_kwh, 2),
            'performance_ratio': round(performance_ratio, 3),
            'monthly_energy_kwh': [round(x, 2) for x in monthly_energy_complete],
            'loss_breakdown_kwh': {k: round(v, 2) for k, v in loss_breakdown.items()}
        }
        
        return results

