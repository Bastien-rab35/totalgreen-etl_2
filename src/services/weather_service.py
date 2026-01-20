"""
Service de collecte des données météorologiques depuis OpenWeather API
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WeatherService:
    """Service de récupération des données météorologiques"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def fetch_weather_data(self, city_name: str) -> Optional[Dict]:
        """Récupère les données météo (brutes + parsées)"""
        try:
            params = {
                'q': f"{city_name},FR",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Données météo récupérées pour {city_name}")
            return {'raw': data, 'parsed': self._parse_weather_data(data)}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur météo pour {city_name}: {e}")
            return None
    
    def _parse_weather_data(self, raw_data: Dict) -> Dict:
        """Parse les données OpenWeather API 2.5"""
        main = raw_data.get('main', {})
        wind = raw_data.get('wind', {})
        weather = raw_data.get('weather', [{}])[0]
        
        return {
            'temp': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'pressure': main.get('pressure'),
            'humidity': main.get('humidity'),
            'dew_point': None,  # Non dispo API 2.5
            'clouds': raw_data.get('clouds', {}).get('all'),
            'uvi': None,  # Non dispo API 2.5
            'visibility': raw_data.get('visibility'),
            'wind_speed': wind.get('speed'),
            'wind_deg': wind.get('deg'),
            'wind_gust': wind.get('gust'),
            'rain_1h': raw_data.get('rain', {}).get('1h', 0),
            'snow_1h': raw_data.get('snow', {}).get('1h', 0),
            'weather_id': weather.get('id'),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description')
        }
    
    def parse_weather_data(self, raw_data: Dict) -> Dict:
        """Méthode publique pour parser depuis Data Lake"""
        return self._parse_weather_data(raw_data)
