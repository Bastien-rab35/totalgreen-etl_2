"""
Pipeline ETL - Partie 2: Transform → Load (BDD normalisée)
Lit les données non traitées du Data Lake, les transforme et les charge dans la BDD
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
        logging.FileHandler('../logs/etl_transform.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TransformToDB:
    """Pipeline de transformation et chargement en BDD"""
    
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
            
            logger.info("Service de transformation initialisé")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            raise
    
    def transform_and_load(self, raw_entry: dict) -> bool:
        """Transforme et charge une entrée du Data Lake dans la BDD"""
        try:
            lake_id = raw_entry['id']
            city_id = raw_entry['city_id']
            city_name = raw_entry['city_name']
            source = raw_entry['source']
            raw_data = raw_entry['raw_data']
            
            logger.info(f"Transformation {source} - {city_name} (Lake ID: {lake_id})")
            
            # Parser les données selon la source
            parsed_data = {}
            if source == 'openweather':
                parsed_data = self.weather_service.parse_weather_data(raw_data)
            elif source == 'aqicn':
                parsed_data = self.air_quality_service.parse_air_quality_data(raw_data)
            
            if not parsed_data:
                logger.warning(f"Impossible de parser {source} - {city_name}")
                return False
            
            # Charger dans la BDD
            # Note: Cette version charge source par source
            # Pour combiner météo + AQI, il faut grouper par city_id + timestamp
            measure = {
                'city_id': city_id,
                'measured_at': parsed_data.get('measured_at') or datetime.utcnow().isoformat()
            }
            
            if source == 'openweather':
                measure.update({
                    'temperature': parsed_data.get('temperature'),
                    'feels_like': parsed_data.get('feels_like'),
                    'humidity': parsed_data.get('humidity'),
                    'pressure': parsed_data.get('pressure'),
                    'wind_speed': parsed_data.get('wind_speed'),
                    'weather_description': parsed_data.get('description'),
                    'raw_weather_id': lake_id
                })
            elif source == 'aqicn':
                measure.update({
                    'aqi': parsed_data.get('aqi'),
                    'pm25': parsed_data.get('pm25'),
                    'pm10': parsed_data.get('pm10'),
                    'raw_aqi_id': lake_id
                })
            
            success = self.db_service.insert_measure_direct(measure)
            
            if success:
                # Marquer comme traité
                self.data_lake_service.mark_as_processed(lake_id)
                logger.info(f"✓ {source} - {city_name} → BDD")
                return True
            else:
                logger.error(f"✗ Échec insertion {source} - {city_name}")
                return False
            
        except Exception as e:
            logger.error(f"Erreur transformation: {e}")
            return False
    
    def run(self, batch_size: int = 100) -> dict:
        """Traite les données non traitées du Data Lake"""
        start_time = time.time()
        logger.info("="*60)
        logger.info(f"TRANSFORM → BDD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        # Récupérer les données non traitées
        unprocessed_data = self.data_lake_service.get_unprocessed_data(limit=batch_size)
        
        if not unprocessed_data:
            logger.info("Aucune donnée à traiter")
            return {'success': 0, 'errors': 0, 'total': 0, 'duration': 0}
        
        logger.info(f"{len(unprocessed_data)} entrées à traiter")
        
        success_count = 0
        for entry in unprocessed_data:
            if self.transform_and_load(entry):
                success_count += 1
        
        # Stats
        duration = time.time() - start_time
        error_count = len(unprocessed_data) - success_count
        stats = {
            'success': success_count,
            'errors': error_count,
            'total': len(unprocessed_data),
            'duration': round(duration, 2)
        }
        
        # Log ETL
        status = 'success' if error_count == 0 else 'warning' if success_count > 0 else 'error'
        self.db_service.log_etl_execution(
            status=status,
            source='transform',
            records_inserted=success_count,
            duration=duration,
            error_message=f"{error_count} échecs" if error_count > 0 else None
        )
        
        logger.info("="*60)
        logger.info(f"Transformation terminée - {success_count}/{len(unprocessed_data)} - {duration:.2f}s")
        logger.info("="*60)
        
        return stats

def main():
    """Point d'entrée"""
    try:
        pipeline = TransformToDB()
        stats = pipeline.run()
        
        # Code de sortie
        if stats['total'] == 0:
            exit(0)  # Pas de données, OK
        elif stats['errors'] == stats['total']:
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
