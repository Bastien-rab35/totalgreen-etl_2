"""
Pipeline ETL - Partie 1: Extract → Load (Data Lake JSONB)
Collecte les données des APIs et les stocke en JSONB dans Supabase
"""
import logging
import time
import os
from datetime import datetime

from config import config
from services import WeatherService, AirQualityService, DatabaseService, DataLakeService

# Création du dossier logs
os.makedirs('../logs', exist_ok=True)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/etl_extract.log'),
        logging.StreamHandler()
    ]
)

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
            
            logger.info("Service d'extraction initialisé")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            raise
    
    def extract_city_data(self, city: dict) -> bool:
        """Extrait et stocke les données d'une ville dans le Data Lake"""
        city_name = city.get('name')
        city_id = city.get('id')
        logger.info(f"Extraction de {city_name}...")
        
        try:
            success = False
            
            # 1. Extraction Météo
            weather_data = self.weather_service.fetch_weather_data(city_name)
            if weather_data and weather_data.get('raw'):
                raw_weather_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'openweather', weather_data['raw']
                )
                if raw_weather_id:
                    logger.info(f"✓ Météo {city_name} → Data Lake (ID: {raw_weather_id})")
                    success = True
            
            # 2. Extraction Qualité de l'air
            aqi_data = self.air_quality_service.fetch_air_quality_data(city_name)
            if aqi_data and aqi_data.get('raw'):
                raw_aqi_id = self.data_lake_service.store_raw_data(
                    city_id, city_name, 'aqicn', aqi_data['raw']
                )
                if raw_aqi_id:
                    logger.info(f"✓ AQI {city_name} → Data Lake (ID: {raw_aqi_id})")
                    success = True
            
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
        
        success_count = 0
        for city in cities:
            if self.extract_city_data(city):
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
            source='extract',
            records_inserted=success_count,
            duration=duration,
            error_message=f"{error_count} échecs" if error_count > 0 else None
        )
        
        logger.info("="*60)
        logger.info(f"Extraction terminée - {success_count}/{len(cities)} - {duration:.2f}s")
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
        logger.error(f"Erreur fatale: {e}")
        exit(1)

if __name__ == "__main__":
    main()
