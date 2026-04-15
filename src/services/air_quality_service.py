"""
Service de collecte des données de qualité de l'air depuis AQICN API
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AirQualityService:
    """Service de récupération des données de qualité de l'air"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def fetch_air_quality_data(self, city_name: str, aqi_station: str = None) -> Optional[Dict]:
        """Récupère les données AQI (brutes + parsées)
        
        Args:
            city_name: Nom de la ville (pour les logs)
            aqi_station: Station AQICN spécifique (ex: "@8613", "france/rhonealpes/rhone/lyon-centre")
                        Si None, utilise city_name par défaut
        """
        try:
            # Utiliser la station spécifique si fournie, sinon le nom de ville
            endpoint = aqi_station if aqi_station else city_name
            url = f"{self.base_url}/{endpoint}/"
            response = requests.get(url, params={'token': self.api_key}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.warning(f"API AQI status non-OK pour {city_name} (station: {endpoint})")
                return None
            
            logger.info(f"Données AQI récupérées pour {city_name} (station: {endpoint})")
            return {'raw': data, 'parsed': self._parse_aqi_data(data)}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur AQI pour {city_name}: {e}")
            return None
    
    def _parse_aqi_data(self, raw_data: Dict) -> Dict:
        """Parse les données AQICN"""
        data = raw_data.get('data', {})
        iaqi = data.get('iaqi', {})
        
        # Helper pour convertir les valeurs (gérer "-" et autres cas)
        def safe_value(val):
            if val is None or val == "-" or val == "":
                return None
            try:
                return float(val) if isinstance(val, (int, float)) else None
            except (ValueError, TypeError):
                return None
        
        aqi_raw = data.get('aqi')
        aqi_value = safe_value(aqi_raw) if aqi_raw != "-" else None
        
        return {
            'aqi_index': int(aqi_value) if aqi_value is not None else None,
            'pm25': safe_value(iaqi.get('pm25', {}).get('v')),
            'pm10': safe_value(iaqi.get('pm10', {}).get('v')),
            'no2': safe_value(iaqi.get('no2', {}).get('v')),
            'o3': safe_value(iaqi.get('o3', {}).get('v')),
            'so2': safe_value(iaqi.get('so2', {}).get('v')),
            'co': safe_value(iaqi.get('co', {}).get('v')),
            'station_attribution': self._get_attribution(data)
        }
    
    def _get_attribution(self, data: Dict) -> Optional[str]:
        """Extrait l'attribution de la station"""
        attributions = data.get('attributions', [])
        if attributions:
            return attributions[0].get('name')
        return data.get('city', {}).get('name')
    
    def parse_air_quality_data(self, raw_data: Dict) -> Dict:
        """Méthode publique pour parser depuis Data Lake"""
        return self._parse_aqi_data(raw_data)
    
    def get_timestamp(self, raw_data: Dict) -> Optional[datetime]:
        """Extrait le timestamp de l'API (moment réel de la mesure)"""
        data = raw_data.get('data', {})
        time_data = data.get('time', {})
        timestamp = time_data.get('v')  # Unix timestamp
        if timestamp:
            return datetime.fromtimestamp(timestamp)
        return None
