"""
Pipeline ETL - Version BATCH (optionnelle)
Charge le Data Lake toutes les heures, transforme 1×/jour
"""
import logging
from datetime import datetime, timedelta
from etl_pipeline import ETLPipeline
from services import DataLakeService, DatabaseService
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchETLPipeline(ETLPipeline):
    """Pipeline avec traitement batch quotidien"""
    
    def collect_only(self):
        """Collecte uniquement dans le Data Lake (horaire)"""
        logger.info("Mode COLLECT ONLY - Data Lake")
        
        cities = self.db_service.get_all_cities()
        for city in cities:
            city_name = city.get('name')
            city_id = city.get('id')
            
            # Extract
            weather_data, aqi_data = self.extract_data(city_name)
            
            # Load Data Lake seulement
            if weather_data.get('raw'):
                self.data_lake_service.store_raw_data(
                    city_id, city_name, 'openweather', weather_data['raw']
                )
            
            if aqi_data.get('raw'):
                self.data_lake_service.store_raw_data(
                    city_id, city_name, 'aqicn', aqi_data['raw']
                )
            
            logger.info(f"✓ {city_name} collectée")
    
    def process_batch(self):
        """Traite les données non traitées du Data Lake (quotidien)"""
        logger.info("Mode BATCH PROCESSING")
        
        # Récupérer toutes les données non traitées
        unprocessed = self.data_lake_service.client.table('raw_data_lake')\
            .select('*')\
            .eq('processed', False)\
            .execute()
        
        logger.info(f"{len(unprocessed.data)} enregistrements à traiter")
        
        # Grouper par ville et timestamp
        grouped = {}
        for record in unprocessed.data:
            key = f"{record['city_id']}_{record['collected_at'][:13]}"  # Par heure
            if key not in grouped:
                grouped[key] = {'weather': None, 'aqi': None, 'city_id': record['city_id']}
            
            if record['source'] == 'openweather':
                grouped[key]['weather'] = record
            else:
                grouped[key]['aqi'] = record
        
        # Transformer et charger
        success = 0
        for key, data in grouped.items():
            if data['weather'] and data['aqi']:
                # Parse et insère
                weather_parsed = self.weather_service._parse_weather_data(data['weather']['raw_data'])
                aqi_parsed = self.air_quality_service._parse_aqi_data(data['aqi']['raw_data'])
                
                inserted = self.db_service.insert_measure(
                    data['city_id'],
                    weather_parsed,
                    aqi_parsed,
                    data['weather']['id'],
                    data['aqi']['id']
                )
                
                if inserted:
                    self.data_lake_service.mark_as_processed(data['weather']['id'])
                    self.data_lake_service.mark_as_processed(data['aqi']['id'])
                    success += 1
        
        logger.info(f"✓ Batch terminé: {success} mesures insérées")

if __name__ == "__main__":
    import sys
    
    pipeline = BatchETLPipeline()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        # Mode batch (quotidien)
        pipeline.process_batch()
    else:
        # Mode collect (horaire)
        pipeline.collect_only()
