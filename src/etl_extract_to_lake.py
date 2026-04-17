"""
Pipeline ETL - Partie 1: Extract → Load (Data Lake JSONB)
Collecte les données des APIs et les stocke en JSONB dans Supabase
"""
import logging
import time
import os
import json
from pathlib import Path
from datetime import datetime

from config import config, setup_logging
from services import WeatherService, AirQualityService, DatabaseService, DataLakeService, TomTomService, HubeauService
import uuid

# Création du dossier logs
os.makedirs('../logs', exist_ok=True)

# Configuration logging
setup_logging()

logger = logging.getLogger(__name__)

class ExtractToLake:
    """Pipeline d'extraction vers Data Lake"""
    
    def __init__(self):
        """Initialise les services"""
        try:
            config.validate()
            
            self.weather_service = WeatherService(
                config.OPENWEATHER_API_KEY,
                config.OPENWEATHER_BASE_URL
            )
            
            self.air_quality_service = AirQualityService(
                config.AQICN_API_KEY,
                config.AQICN_BASE_URL
            )
            
            self.db_service = DatabaseService(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
            
            self.data_lake_service = DataLakeService(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
            
            self.tomtom_service = TomTomService(
                config.TOMTOM_API_KEY,
                config.TOMTOM_FLOW_BASE_URL,
                config.TOMTOM_INCIDENTS_BASE_URL
            )
            
            self.hubeau_service = HubeauService(
                config.HUBEAU_EAU_POTABLE_URL,
                config.HUBEAU_CD_STATIONS_URL,
                config.HUBEAU_CD_OBSERVATIONS_URL
            )

            self.aqi_station_map = self._load_aqi_station_map()
            
            # Pour regrouper les appels TomTom avec le même traffic model (passe par exécution)
            self.current_traffic_model_id = str(uuid.uuid4())
            
            logger.info("Service d'extraction initialisé")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            raise

    def _load_aqi_station_map(self) -> dict:
        """Charge le mapping des stations AQI depuis le référentiel local."""
        try:
            ref_path = Path(__file__).resolve().parent.parent / 'data' / 'cities_reference.json'
            with open(ref_path, 'r', encoding='utf-8') as f:
                cities_ref = json.load(f)

            mapping = {}
            for row in cities_ref:
                station = row.get('aqi_station')
                city_id = row.get('id')
                city_name = row.get('name')
                if not station:
                    continue
                if city_id is not None:
                    mapping[city_id] = station
                if city_name:
                    mapping[city_name] = station

            logger.info(f"Référentiel AQI chargé: {len(cities_ref)} villes")
            return mapping
        except Exception as e:
            logger.warning(f"Impossible de charger le référentiel AQI local: {e}")
            return {}

    def _resolve_aqi_station(self, city: dict) -> str:
        """Résout la station AQI à utiliser (BDD puis fallback référentiel local)."""
        station = city.get('aqi_station')
        if station:
            return station

        city_id = city.get('id')
        city_name = city.get('name')
        return self.aqi_station_map.get(city_id) or self.aqi_station_map.get(city_name)
    
    def extract_city_data(self, city: dict) -> bool:
        """Extrait et stocke les données d'une ville dans le Data Lake"""
        city_name = city.get('name')
        city_id = city.get('id')
        aqi_station = self._resolve_aqi_station(city)
        logger.info(f"Extraction de {city_name}...")
        
        try:
            success = False
            weather_success = False
            aqi_success = False
            
            # 1. Extraction Météo
            weather_data = self.weather_service.fetch_weather_data(city_name)
            if weather_data and weather_data.get('raw'):
                # Extraire le timestamp réel de l'API
                weather_timestamp = self.weather_service.get_timestamp(weather_data['raw'])
                raw_weather_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'openweather', weather_data['raw'], weather_timestamp
                )
                if raw_weather_id:
                    logger.info(f"✓ Météo {city_name} → Data Lake (ID: {raw_weather_id})")
                    success = True
                    weather_success = True
            
            # 2. Extraction Qualité de l'air (avec station spécifique)
            aqi_data = self.air_quality_service.fetch_air_quality_data(city_name, aqi_station)
            if aqi_data and aqi_data.get('raw'):
                # Extraire le timestamp réel de l'API
                aqi_timestamp = self.air_quality_service.get_timestamp(aqi_data['raw'])
                raw_aqi_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'aqicn', aqi_data['raw'], aqi_timestamp
                )
                if raw_aqi_id:
                    logger.info(f"✓ AQI {city_name} → Data Lake (ID: {raw_aqi_id})")
                    success = True
                    aqi_success = True

            if weather_success and not aqi_success:
                logger.error(f"✗ AQI absent pour {city_name} (station: {aqi_station})")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur extraction {city_name}: {e}")
            return False
    
    def run(self) -> dict:
        """Exécute l'extraction pour toutes les villes"""
        start_time = time.time()
        logger.info("="*60)
        logger.info(f"EXTRACTION → DATA LAKE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        cities = self.db_service.get_all_cities()
        if not cities:
            logger.error("Aucune ville trouvée")
            return {'success': 0, 'errors': 0, 'total': 0, 'duration': 0}
        
        logger.info(f"{len(cities)} villes à extraire")
        
        city_success_count = 0
        weather_inserted_count = 0
        aqi_inserted_count = 0
        aqi_failure_count = 0
        tomtom_inserted_count = 0
        hubeau_inserted_count = 0
        
        for city in cities:
            city_name = city.get('name')
            city_id = city.get('id')
            lat = city.get('latitude')
            lon = city.get('longitude')
            
            aqi_station = self._resolve_aqi_station(city)
            weather_data = self.weather_service.fetch_weather_data(city_name)
            aqi_data = self.air_quality_service.fetch_air_quality_data(city_name, aqi_station)

            if weather_data and weather_data.get('raw'):
                weather_timestamp = self.weather_service.get_timestamp(weather_data['raw'])
                raw_weather_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'openweather', weather_data['raw'], weather_timestamp
                )
                if raw_weather_id:
                    weather_inserted_count += 1

            if aqi_data and aqi_data.get('raw'):
                aqi_timestamp = self.air_quality_service.get_timestamp(aqi_data['raw'])
                raw_aqi_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'aqicn', aqi_data['raw'], aqi_timestamp
                )
                if raw_aqi_id:
                    aqi_inserted_count += 1
            else:
                aqi_failure_count += 1

            # --- EXTRACT: TomTom ---
            if lat and lon:
                bbox_tt = f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}"
                
                # Incidents
                incidents = self.tomtom_service.get_traffic_incidents(city_name, bbox_tt, self.current_traffic_model_id)
                for inc in incidents[:30]:
                    if self.data_lake_service.store_raw_data(city_id, city_name, 'tomtom_incidents', inc):
                        tomtom_inserted_count += 1
                        
                # Flow (Vitesse sur 3 axes par ville pour représentativité)
                points = [("C", lat, lon), ("E", lat, lon+0.02), ("W", lat, lon-0.02)]
                for suf, p_lat, p_lon in points:
                    flow = self.tomtom_service.get_traffic_flow(
                        f"{city_name[:3].upper()}_{suf}", city_name, p_lat, p_lon, self.current_traffic_model_id
                    )
                    if flow:
                        if self.data_lake_service.store_raw_data(city_id, city_name, 'tomtom_flow', flow):
                            tomtom_inserted_count += 1

            # --- EXTRACT: Hub'Eau (Qualité Eau Potable et Cours d'Eau) ---
            if city_name:
                # 1. Eau Potable
                eau_potable_results = self.hubeau_service.get_eau_potable(city_name)
                for result in eau_potable_results[:20]:
                    if self.data_lake_service.store_raw_data(city_id, city_name, 'hubeau_eau_potable', result):
                        hubeau_inserted_count += 1
                        
            if lat and lon:
                bbox_he = f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}"
                
                # 2. Stations Cours d'eau
                stations_cd = self.hubeau_service.get_cours_deau_stations(bbox_he)
                for st in stations_cd:
                    if self.data_lake_service.store_raw_data(city_id, city_name, 'hubeau_cd_stations', st):
                        hubeau_inserted_count += 1
                        
                # 3. Observations sur les stations de cours d'eau (limite à 3 stations)
                for st in stations_cd[:1]:
                    code_station = st.get('code_station')
                    if code_station:
                        observations = self.hubeau_service.get_cours_deau_observations(code_station)
                        for obs in observations:
                            if self.data_lake_service.store_raw_data(city_id, city_name, 'hubeau_cd_observations', obs):
                                hubeau_inserted_count += 1

            if weather_data and weather_data.get('raw'):
                city_success_count += 1
            time.sleep(1)  # Respect des limites API
        
        # Stats
        duration = time.time() - start_time
        error_count = len(cities) - city_success_count
        stats = {
            'success': city_success_count,
            'errors': error_count,
            'total': len(cities),
            'weather_inserted': weather_inserted_count,
            'aqi_inserted': aqi_inserted_count,
            'aqi_errors': aqi_failure_count,
            'tomtom_inserted': tomtom_inserted_count,
            'hubeau_inserted': hubeau_inserted_count,
            'duration': round(duration, 2)
        }
        
        # Log ETL
        status = 'success' if error_count == 0 else 'warning' if city_success_count > 0 else 'error'
        self.db_service.log_etl_execution(
            status=status,
            source='extract',
            records_inserted=city_success_count,
            duration=duration,
            error_message=(f"{error_count} échecs; AQI: {aqi_inserted_count}/{len(cities)} villes" if (error_count > 0 or aqi_failure_count > 0) else None)
        )
        
        logger.info("="*60)
        logger.info(f"Extraction terminée - {city_success_count}/{len(cities)} villes, météo: {weather_inserted_count}, AQI: {aqi_inserted_count} - {duration:.2f}s")
        logger.info("="*60)
        
        return stats

def main():
    """Point d'entrée"""
    try:
        pipeline = ExtractToLake()
        stats = pipeline.run()
        
        # Code de sortie
        if stats['errors'] == stats['total']:
            exit(1)  # Échec complet
        elif stats['errors'] > 0:
            exit(2)  # Échec partiel
        else:
            exit(0)  # Succès
            
    except Exception as e:
        logger.exception(f"Erreur fatale: {e}")
        exit(1)

if __name__ == "__main__":
    main()
