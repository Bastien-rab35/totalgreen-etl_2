"""
Service de collecte des données météorologiques depuis OpenWeather API
"""
import requests
import logging
import json
from datetime import datetime, timezone
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

            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Réponse météo invalide pour {city_name}: JSON string non parsable")
                    return None

            if not isinstance(data, dict):
                logger.error(f"Réponse météo invalide pour {city_name}: type inattendu {type(data).__name__}")
                return None
            
            logger.info(f"Données météo récupérées pour {city_name}")
            return {'raw': data, 'parsed': self._parse_weather_data(data)}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur météo pour {city_name}: {e}")
            return None
    
    def _parse_weather_data(self, raw_data: Dict) -> Dict:
        """Parse les données OpenWeather API 2.5"""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return {}

        if not isinstance(raw_data, dict):
            return {}

        main = raw_data.get('main', {})
        wind = raw_data.get('wind', {})
        clouds = raw_data.get('clouds', {})
        rain = raw_data.get('rain', {})
        snow = raw_data.get('snow', {})
        weather = raw_data.get('weather', [{}])

        if not isinstance(main, dict):
            main = {}
        if not isinstance(wind, dict):
            wind = {}
        if not isinstance(clouds, dict):
            clouds = {}
        if not isinstance(rain, dict):
            rain = {}
        if not isinstance(snow, dict):
            snow = {}
        if not isinstance(weather, list) or not weather:
            weather = [{}]

        weather = weather[0] if isinstance(weather[0], dict) else {}
        
        return {
            'temp': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'pressure': main.get('pressure'),
            'humidity': main.get('humidity'),
            'dew_point': None,  # Non dispo API 2.5
            'clouds': clouds.get('all'),
            'uvi': None,  # Non dispo API 2.5
            'visibility': raw_data.get('visibility'),
            'wind_speed': wind.get('speed'),
            'wind_deg': wind.get('deg'),
            'wind_gust': wind.get('gust'),
            'rain_1h': rain.get('1h', 0),
            'snow_1h': snow.get('1h', 0),
            'weather_id': weather.get('id'),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description')
        }
    
    def get_timestamp(self, raw_data: Dict) -> Optional[datetime]:
        """Extrait le timestamp de l'API (moment réel de la mesure)"""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return None

        if not isinstance(raw_data, dict):
            return None

        timestamp = raw_data.get('dt')
        if timestamp is not None:
            try:
                # OpenWeather fournit un timestamp UNIX en UTC.
                return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                return None
        return None
    
    def parse_weather_data(self, raw_data: Dict) -> Dict:
        """Méthode publique pour parser depuis Data Lake"""
        return self._parse_weather_data(raw_data)
