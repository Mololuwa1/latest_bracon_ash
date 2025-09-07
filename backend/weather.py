"""
Weather data integration for Heliotelligence
Fetches Typical Meteorological Year (TMY) data from PVGIS API
"""

import requests
import pandas as pd
import io
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def get_pvgis_tmy(latitude: float, longitude: float) -> pd.DataFrame:
    """
    Fetch Typical Meteorological Year weather data from PVGIS API for UK coordinates.
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        
    Returns:
        pandas DataFrame with columns ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
        and datetime index
        
    Raises:
        requests.RequestException: If API request fails
        ValueError: If coordinates are outside UK bounds or data parsing fails
    """
    
    # Validate UK coordinates (approximate bounds)
    if not (49.5 <= latitude <= 61.0 and -8.5 <= longitude <= 2.0):
        raise ValueError(f"Coordinates ({latitude}, {longitude}) appear to be outside UK bounds")
    
    # PVGIS API endpoint for TMY data
    base_url = "https://re.jrc.ec.europa.eu/api/tmy"
    
    params = {
        'lat': latitude,
        'lon': longitude,
        'outputformat': 'csv',
        'usehorizon': 1,  # Use horizon data
        'userhorizon': '',  # No user-defined horizon
        'startyear': 2005,  # Default TMY period
        'endyear': 2016,
        'map_variables': 1,  # Include variable mapping
        'browser': 0  # Machine-readable format
    }
    
    try:
        logger.info(f"Fetching TMY data for coordinates: {latitude}, {longitude}")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse CSV response
        # PVGIS returns CSV with metadata at the top, data starts after header line
        content = response.text
        
        # Find the start of actual data (after the header comments)
        lines = content.split('\n')
        data_start_idx = None
        
        for i, line in enumerate(lines):
            if line.startswith('time(UTC),T2m,RH,G(h),Gb(n),Gd(h)'):
                data_start_idx = i
                break
        
        if data_start_idx is None:
            raise ValueError("Could not find data header in PVGIS response")
        
        # Extract data portion (stop at first empty line after header)
        data_lines = [lines[data_start_idx]]  # Include header
        for i in range(data_start_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line:  # Stop at first empty line
                break
            data_lines.append(lines[i])
        
        data_csv = '\n'.join(data_lines)
        
        # Read into DataFrame
        df = pd.read_csv(io.StringIO(data_csv))
        
        # Rename columns to match expected format
        column_mapping = {
            'time(UTC)': 'datetime',
            'T2m': 'temp_air',          # Air temperature at 2m (°C)
            'G(h)': 'ghi',              # Global horizontal irradiance (W/m²)
            'Gb(n)': 'dni',             # Direct normal irradiance (W/m²)
            'Gd(h)': 'dhi',             # Diffuse horizontal irradiance (W/m²)
            'WS10m': 'wind_speed'       # Wind speed at 10m (m/s)
        }
        
        # Check if all required columns exist
        missing_cols = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing expected columns in PVGIS data: {missing_cols}")
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Select only required columns
        required_cols = ['datetime', 'ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
        df = df[required_cols]
        
        # Parse datetime and set as index
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d:%H%M')
        df = df.set_index('datetime')
        
        # Validate data quality
        if df.empty:
            raise ValueError("No weather data received from PVGIS")
        
        if len(df) < 8000:  # Should have ~8760 hours for a full year
            logger.warning(f"Received only {len(df)} hours of data, expected ~8760")
        
        # Check for missing values
        missing_data = df.isnull().sum()
        if missing_data.any():
            logger.warning(f"Missing data found: {missing_data.to_dict()}")
            # Fill missing values with interpolation
            df = df.interpolate(method='linear')
        
        # Ensure non-negative irradiance values
        irradiance_cols = ['ghi', 'dni', 'dhi']
        for col in irradiance_cols:
            df[col] = df[col].clip(lower=0)
        
        logger.info(f"Successfully fetched {len(df)} hours of TMY data")
        logger.info(f"Data range: {df.index[0]} to {df.index[-1]}")
        
        return df
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from PVGIS API: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing PVGIS data: {e}")
        raise ValueError(f"Failed to process weather data: {e}")


def validate_weather_data(df: pd.DataFrame) -> bool:
    """
    Validate weather data DataFrame format and content.
    
    Args:
        df: Weather data DataFrame
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_columns = ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
    
    # Check columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check data types
    for col in required_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column {col} must be numeric")
    
    # Check for reasonable value ranges
    if (df['ghi'] < 0).any() or (df['ghi'] > 1500).any():
        raise ValueError("GHI values outside reasonable range (0-1500 W/m²)")
    
    if (df['temp_air'] < -50).any() or (df['temp_air'] > 60).any():
        raise ValueError("Temperature values outside reasonable range (-50 to 60°C)")
    
    if (df['wind_speed'] < 0).any() or (df['wind_speed'] > 50).any():
        raise ValueError("Wind speed values outside reasonable range (0-50 m/s)")
    
    return True

