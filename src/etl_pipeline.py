"""
Pipeline ETL pour la collecte de données environnementales
Architecture: Extract → Load (Data Lake JSONB) → Transform → Load (BDD)
"""
import logging
import time
import os
from datetime import datetime
from typing import Tuple

from config import config
from services import WeatherService, AirQualityService, DatabaseService, DataLakeService

# Création du dossier logs
os.makedirs('../logs', exist_ok=True)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ETLPipeline:
    """Pipeline ETL - Extract Load Transform"""
    
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
            
            logger.info("Pipeline ETL initialisé")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            raise
    
    def extract_data(self, city_name: str, aqi_station: str = None) -> Tuple[dict, dict]:
        """Extrait les données météo et AQI (brutes + parsées)"""
        weather_data = self.weather_service.fetch_weather_data(city_name)
        aqi_data = self.air_quality_service.fetch_air_quality_data(city_name, aqi_station)
        return weather_data or {}, aqi_data or {}
    
    def process_city(self, city: dict) -> bool:
        """Traite une ville: Extract → Load (Data Lake) → Transform → Load (BDD)"""
        city_name = city.get('name')
        city_id = city.get('id')
        aqi_station = city.get('aqi_station')  # Station AQICN spécifique
        logger.info(f"Traitement de {city_name}...")
        
        try:
            # 1. EXTRACT
            weather_data, aqi_data = self.extract_data(city_name, aqi_station)
            if not weather_data and not aqi_data:
                logger.warning(f"Aucune donnée pour {city_name}")
                return False
            
            # 2. LOAD Data Lake (JSONB)
            raw_weather_id = None
            raw_aqi_id = None
            
            if weather_data.get('raw'):
                raw_weather_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'openweather', weather_data['raw']
                )
            
            if aqi_data.get('raw'):
                raw_aqi_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'aqicn', aqi_data['raw']
                )
            
            # 3. TRANSFORM & LOAD BDD
            success = self.db_service.insert_measure(
                city_id, 
                weather_data.get('parsed', {}), 
                aqi_data.get('parsed', {}),
                raw_weather_id,
                raw_aqi_id
            )
            
            # 4. Marquer comme traité
            if success:
                if raw_weather_id:
                    self.data_lake_service.mark_as_processed(raw_weather_id)
                if raw_aqi_id:
                    self.data_lake_service.mark_as_processed(raw_aqi_id)
                logger.info(f"✓ {city_name} traitée")
            else:
                logger.error(f"✗ Échec {city_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur {city_name}: {e}")
            return False
    
    def run(self) -> dict:
        """Exécute le pipeline complet"""
        start_time = time.time()
        logger.info("="*60)
        logger.info(f"Pipeline ETL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        cities = self.db_service.get_all_cities()
        if not cities:
            logger.error("Aucune ville trouvée")
            return {'success': 0, 'errors': 0, 'total': 0, 'duration': 0}
        
        logger.info(f"{len(cities)} villes à traiter")
        
        success_count = 0
        for city in cities:
            if self.process_city(city):
                success_count += 1
            time.sleep(1)  # Respect des limites API
        
        # Stats
        duration = time.time() - start_time
        error_count = len(cities) - success_count
        stats = {
            'success': success_count,
            'errors': error_count,
            'total': len(cities),
            'duration': round(duration, 2)
        }
        
        # Log ETL
        status = 'success' if error_count == 0 else 'warning' if success_count > 0 else 'error'
        self.db_service.log_etl_execution(
            status=status,
            source='both',
            records_inserted=success_count,
            duration=duration,
            error_message=f"{error_count} échecs" if error_count > 0 else None
        )
        
        logger.info("="*60)
        logger.info(f"Pipeline terminé - {success_count}/{len(cities)} - {duration:.2f}s")
        logger.info("="*60)
        
        return stats

def main():
    """Point d'entrée"""
    try:
        pipeline = ETLPipeline()
        stats = pipeline.run()
        
        # Code de sortie
        if stats['errors'] == stats['total']:
            exit(1)  # Échec complet
        elif stats['errors'] > 0:
            exit(2)  # Échec partiel
        else:
            exit(0)  # Succès
            
    except Exception as e:
        logger.critical(f"Erreur critique: {e}")
        exit(1)

if __name__ == "__main__":
    main()
