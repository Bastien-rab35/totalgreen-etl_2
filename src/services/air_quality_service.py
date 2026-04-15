"""
Service de collecte des données de qualité de l'air depuis AQICN API
"""
import requests
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AirQualityService:
    """Service de récupération des données de qualité de l'air"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def _candidate_endpoints(self, city_name: str, aqi_station: str = None) -> list:
        """Construit les endpoints AQICN à essayer, du plus précis au plus générique."""
        candidates = []

        if aqi_station:
            candidates.append(aqi_station.strip().strip('/'))

        normalized_city = city_name.strip().strip('/')
        candidates.append(normalized_city)

        # Fallback simple pour les cas où la casse ou les espaces posent problème.
        lower_city = normalized_city.lower()
        if lower_city not in candidates:
            candidates.append(lower_city)

        seen = set()
        ordered = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
        return ordered
    
    def fetch_air_quality_data(self, city_name: str, aqi_station: str = None) -> Optional[Dict]:
        """Récupère les données AQI (brutes + parsées)
        
        Args:
            city_name: Nom de la ville (pour les logs)
            aqi_station: Station AQICN spécifique (ex: "@8613", "france/rhonealpes/rhone/lyon-centre")
                        Si None, utilise city_name par défaut
        """
        last_error = None

        for endpoint in self._candidate_endpoints(city_name, aqi_station):
            try:
                url = f"{self.base_url}/{endpoint}/"
                response = requests.get(url, params={'token': self.api_key}, timeout=10)

                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(f"AQI {city_name}: {last_error} sur {endpoint}")
                    continue

                data = response.json()

                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        last_error = "JSON string non parsable"
                        logger.warning(f"Erreur parsing AQI pour {city_name} (station: {endpoint}): {last_error}")
                        continue

                if not isinstance(data, dict):
                    last_error = f"type inattendu {type(data).__name__}"
                    logger.warning(f"Erreur parsing AQI pour {city_name} (station: {endpoint}): {last_error}")
                    continue

                if data.get('status') != 'ok':
                    error_payload = data.get('data')
                    if isinstance(error_payload, dict):
                        last_error = error_payload.get('message') or str(error_payload)
                    elif error_payload is not None:
                        last_error = str(error_payload)
                    else:
                        last_error = 'status non-ok'
                    logger.warning(f"API AQI status non-OK pour {city_name} (station: {endpoint}) - {last_error}")
                    continue

                logger.info(f"Données AQI récupérées pour {city_name} (station: {endpoint})")
                return {'raw': data, 'parsed': self._parse_aqi_data(data)}

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"Erreur AQI pour {city_name} (station: {endpoint}): {e}")
            except ValueError as e:
                last_error = f"JSON invalide: {e}"
                logger.warning(f"Erreur parsing AQI pour {city_name} (station: {endpoint}): {e}")

        logger.error(f"AQI indisponible pour {city_name} après essais: {self._candidate_endpoints(city_name, aqi_station)} - dernier retour: {last_error}")
        return None
    
    def _parse_aqi_data(self, raw_data: Dict) -> Dict:
        """Parse les données AQICN"""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return {}

        if not isinstance(raw_data, dict):
            return {}

        data = raw_data.get('data', {})
        if not isinstance(data, dict):
            data = {}

        iaqi = data.get('iaqi', {})
        if not isinstance(iaqi, dict):
            iaqi = {}

        def iaqi_value(key: str):
            node = iaqi.get(key)
            if isinstance(node, dict):
                return safe_value(node.get('v'))
            return safe_value(node)
        
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
            'pm25': iaqi_value('pm25'),
            'pm10': iaqi_value('pm10'),
            'no2': iaqi_value('no2'),
            'o3': iaqi_value('o3'),
            'so2': iaqi_value('so2'),
            'co': iaqi_value('co'),
            'station_attribution': self._get_attribution(data)
        }
    
    def _get_attribution(self, data: Dict) -> Optional[str]:
        """Extrait l'attribution de la station"""
        attributions = data.get('attributions', [])
        if isinstance(attributions, list) and attributions:
            first = attributions[0]
            if isinstance(first, dict):
                return first.get('name')

        city = data.get('city', {})
        if isinstance(city, dict):
            return city.get('name')
        if isinstance(city, str):
            return city
        return None
    
    def parse_air_quality_data(self, raw_data: Dict) -> Dict:
        """Méthode publique pour parser depuis Data Lake"""
        return self._parse_aqi_data(raw_data)
    
    def get_timestamp(self, raw_data: Dict) -> Optional[datetime]:
        """Extrait le timestamp de l'API (moment réel de la mesure)"""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return None

        if not isinstance(raw_data, dict):
            return None

        data = raw_data.get('data', {})
        if not isinstance(data, dict):
            return None

        time_data = data.get('time', {})
        if not isinstance(time_data, dict):
            return None

        # 1) Le champ ISO inclut déjà le fuseau (ex: 2026-04-15T10:00:00+02:00)
        iso_ts = time_data.get('iso')
        if isinstance(iso_ts, str) and iso_ts:
            try:
                dt = datetime.fromisoformat(iso_ts.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass

        # 2) Fallback sur "s" + "tz" si dispo
        s_ts = time_data.get('s')
        tz_ts = time_data.get('tz')
        if isinstance(s_ts, str) and s_ts:
            candidates = []
            if isinstance(tz_ts, str) and tz_ts:
                tz_value = tz_ts if tz_ts[0] in ('+', '-') else f"+{tz_ts}"
                candidates.append(f"{s_ts}{tz_value}")
                candidates.append(f"{s_ts} {tz_value}")
            candidates.append(s_ts)

            for candidate in candidates:
                try:
                    dt = datetime.fromisoformat(candidate)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc)
                except ValueError:
                    continue

        # 3) Dernier fallback sur timestamp UNIX
        unix_ts = time_data.get('v')
        if unix_ts is not None:
            try:
                return datetime.fromtimestamp(float(unix_ts), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                return None
        return None
