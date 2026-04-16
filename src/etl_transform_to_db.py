"""
Pipeline ETL - Partie 2: Transform → Load (BDD normalisée)
Lit les données non traitées du Data Lake, les transforme et les charge dans la BDD
Intègre la détection d'anomalies ML (Isolation Forest + règles métier)
"""
import logging
import time
import os
import numpy as np
from datetime import datetime, timezone

from config import config
from services import WeatherService, AirQualityService, DatabaseService, DataLakeService
from services.anomaly_detection_service import AnomalyDetectionService, format_anomaly_for_db

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
            
            # Service de détection d'anomalies ML
            self.anomaly_service = AnomalyDetectionService(contamination=0.05)
            self._train_anomaly_model()
            
            logger.info("Service de transformation initialisé (avec ML anomaly detection)")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation: {e}")
            raise
    
    def _train_anomaly_model(self):
        """Entraîne le modèle Isolation Forest sur les données historiques"""
        try:
            logger.info("⚡ Entraînement du modèle ML (Isolation Forest)...")
            
            # Récupérer données historiques
            historical_data = self.db_service.get_historical_data_for_ml(limit=5000)
            
            if historical_data:
                # Convertir en numpy array
                X = np.array(historical_data)
                
                # Entraîner le modèle
                self.anomaly_service.train_isolation_forest(X)
                logger.info(f"✓ Modèle ML entraîné sur {len(historical_data)} mesures")
            else:
                logger.warning("⚠️  Pas assez de données historiques pour ML (min: 100). Détection ML désactivée.")
                
        except Exception as e:
            logger.error(f"Erreur entraînement modèle ML: {e}")
    
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
            # Utiliser le timestamp du data lake (celui de l'API)
            measure = {
                'city_id': city_id,
                'captured_at': raw_entry.get('collected_at', datetime.now(timezone.utc).isoformat())
            }
            
            if source == 'openweather':
                measure.update({
                    'temp': parsed_data.get('temp'),
                    'feels_like': parsed_data.get('feels_like'),
                    'humidity': parsed_data.get('humidity'),
                    'pressure': parsed_data.get('pressure'),
                    'wind_speed': parsed_data.get('wind_speed'),
                    'wind_deg': parsed_data.get('wind_deg'),
                    'wind_gust': parsed_data.get('wind_gust'),
                    'clouds': parsed_data.get('clouds'),
                    'visibility': parsed_data.get('visibility'),
                    'rain_1h': parsed_data.get('rain_1h'),
                    'snow_1h': parsed_data.get('snow_1h'),
                    'weather_id': parsed_data.get('weather_id'),
                    'weather_main': parsed_data.get('weather_main'),
                    'weather_description': parsed_data.get('weather_description'),
                    'raw_weather_id': lake_id
                })
            elif source == 'aqicn':
                measure.update({
                    'aqi_index': parsed_data.get('aqi_index'),
                    'pm25': parsed_data.get('pm25'),
                    'pm10': parsed_data.get('pm10'),
                    'no2': parsed_data.get('no2'),
                    'o3': parsed_data.get('o3'),
                    'so2': parsed_data.get('so2'),
                    'co': parsed_data.get('co'),
                    'station_attribution': parsed_data.get('station_attribution'),
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
    
    def group_by_city_and_time(self, data_list: list) -> tuple:
        """Groupe les entrées data lake par (city_id, heure) et dédoublonne par source.

        Pour un même (ville, heure, source), conserve l'entrée la plus récente
        et retourne la liste des IDs écartés pour les marquer comme traités.
        """
        from collections import defaultdict

        grouped = defaultdict(lambda: {'weather': None, 'aqi': None})
        discarded_ids = set()
        now = datetime.utcnow()

        for entry in data_list:
            city_id = entry['city_id']
            timestamp_str = entry.get('collected_at', '')
            if timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                dt = now

            hour_key = dt.replace(minute=0, second=0, microsecond=0).isoformat()
            key = (city_id, hour_key)

            if entry['source'] == 'openweather':
                source_key = 'weather'
            elif entry['source'] == 'aqicn':
                source_key = 'aqi'
            else:
                logger.warning(f"Source inconnue ignorée dans le grouping: {entry.get('source')}")
                discarded_ids.add(entry['id'])
                continue

            current = grouped[key][source_key]
            if current is None:
                grouped[key][source_key] = entry
            else:
                # Conserver l'entrée la plus récente pour une même source sur la même heure.
                if entry['id'] > current['id']:
                    discarded_ids.add(current['id'])
                    grouped[key][source_key] = entry
                else:
                    discarded_ids.add(entry['id'])

        # Log des mesures incomplètes (normal: une API peut être temporairement indisponible)
        for key, data in grouped.items():
            if data['weather'] is None or data['aqi'] is None:
                city_id, timestamp = key
                missing = 'weather' if data['weather'] is None else 'aqi'
                age_info = ""
                if data['weather']:
                    dt = datetime.fromisoformat(data['weather']['collected_at'].replace('Z', '+00:00'))
                    age = (now - dt.replace(tzinfo=None)).total_seconds() / 3600
                    age_info = f" (âge: {age:.1f}h)"
                elif data['aqi']:
                    dt = datetime.fromisoformat(data['aqi']['collected_at'].replace('Z', '+00:00'))
                    age = (now - dt.replace(tzinfo=None)).total_seconds() / 3600
                    age_info = f" (âge: {age:.1f}h)"
                logger.warning(f"⏳ Mesure incomplète: City {city_id} @ {timestamp[:19]} - manque {missing}{age_info}")

        return grouped, discarded_ids
    
    def transform_and_load_combined(self, weather_entry: dict, aqi_entry: dict) -> bool:
        """Transforme et charge une mesure combinée météo + AQI"""
        try:
            # Utiliser weather comme base (toujours présent en priorité)
            base_entry = weather_entry if weather_entry else aqi_entry
            city_id = base_entry['city_id']
            city_name = base_entry['city_name']
            captured_at = base_entry.get('collected_at', datetime.utcnow().isoformat())
            
            logger.info(f"Transformation combinée - {city_name} @ {captured_at[:19]}")
            
            # Créer la measure de base
            measure = {
                'city_id': city_id,
                'captured_at': captured_at
            }
            
            # Ajouter les données météo si disponibles
            if weather_entry:
                raw_data = weather_entry['raw_data']
                parsed = self.weather_service.parse_weather_data(raw_data)
                if parsed:
                    measure.update({
                        'temp': parsed.get('temp'),
                        'feels_like': parsed.get('feels_like'),
                        'humidity': parsed.get('humidity'),
                        'pressure': parsed.get('pressure'),
                        'wind_speed': parsed.get('wind_speed'),
                        'wind_deg': parsed.get('wind_deg'),
                        'wind_gust': parsed.get('wind_gust'),
                        'clouds': parsed.get('clouds'),
                        'visibility': parsed.get('visibility'),
                        'rain_1h': parsed.get('rain_1h'),
                        'snow_1h': parsed.get('snow_1h'),
                        'weather_id': parsed.get('weather_id'),
                        'weather_main': parsed.get('weather_main'),
                        'weather_description': parsed.get('weather_description'),
                        'raw_weather_id': weather_entry['id']
                    })
            
            # Ajouter les données AQI si disponibles
            if aqi_entry:
                raw_data = aqi_entry['raw_data']
                parsed = self.air_quality_service.parse_air_quality_data(raw_data)
                if parsed:
                    measure.update({
                        'aqi_index': parsed.get('aqi_index'),
                        'pm25': parsed.get('pm25'),
                        'pm10': parsed.get('pm10'),
                        'no2': parsed.get('no2'),
                        'o3': parsed.get('o3'),
                        'so2': parsed.get('so2'),
                        'co': parsed.get('co'),
                        'station_attribution': parsed.get('station_attribution'),
                        'raw_aqi_id': aqi_entry['id']
                    })
            
            # ⚡ DÉTECTION D'ANOMALIES ML
            anomalies_detected = []
            anomaly_score = 0.0
            
            # Préparer les données pour analyse
            measure_for_analysis = {
                'temperature': measure.get('temp'),
                'feels_like': measure.get('feels_like'),
                'humidity': measure.get('humidity'),
                'pressure': measure.get('pressure'),
                'wind_speed': measure.get('wind_speed'),
                'aqi': measure.get('aqi_index'),
                'pm2_5': measure.get('pm25'),
                'pm10': measure.get('pm10')
            }
            
            # Récupérer statistiques de la ville
            city_stats = self.db_service.get_city_statistics(city_name, days=30)
            
            # Détecter les anomalies
            is_anomaly, anomalies_list, max_score = self.anomaly_service.detect_anomalies(
                measure_for_analysis,
                city_stats
            )
            
            if is_anomaly:
                anomalies_detected = anomalies_list
                anomaly_score = max_score
                
                # Log des anomalies
                severity_counts = {}
                for anom in anomalies_list:
                    sev = anom.get('severity', 'unknown')
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                severity_str = ', '.join([f"{k}:{v}" for k, v in severity_counts.items()])
                logger.warning(f"🚨 Anomalies détectées pour {city_name}: {severity_str}")
                
                # Rejeter les mesures avec anomalies critiques
                critical_anomalies = [a for a in anomalies_list if a.get('severity') == 'critical']
                if critical_anomalies:
                    logger.error(f"❌ Mesure rejetée pour {city_name} : {len(critical_anomalies)} anomalies critiques")
                    
                    # Stocker les anomalies critiques
                    for anom in critical_anomalies:
                        anomaly_record = format_anomaly_for_db(anom, city_id, city_name, captured_at)
                        self.db_service.insert_anomaly(anomaly_record)
                    
                    # Marquer comme traité mais ne pas insérer dans fact_measures
                    if weather_entry:
                        self.data_lake_service.mark_as_processed(weather_entry['id'])
                    if aqi_entry:
                        self.data_lake_service.mark_as_processed(aqi_entry['id'])
                    
                    return False  # Mesure rejetée
            
            # Ajouter les flags d'anomalie dans la mesure
            measure['is_anomaly'] = is_anomaly
            measure['anomaly_score'] = anomaly_score if is_anomaly else None
            
            # Insérer dans le modèle en étoile (fact_measures)
            success = self.db_service.insert_into_star_schema(measure)
            
            if success:
                # Marquer toutes les entrées comme traitées
                if weather_entry:
                    self.data_lake_service.mark_as_processed(weather_entry['id'])
                if aqi_entry:
                    self.data_lake_service.mark_as_processed(aqi_entry['id'])
                
                # Stocker les anomalies non-critiques (flagged)
                if anomalies_detected:
                    for anom in anomalies_detected:
                        if anom.get('severity') != 'critical':  # Critiques déjà stockées
                            anomaly_record = format_anomaly_for_db(anom, city_id, city_name, captured_at)
                            self.db_service.insert_anomaly(anomaly_record)
                
                sources = []
                if weather_entry: sources.append('weather')
                if aqi_entry: sources.append('aqi')
                
                anomaly_flag = " 🚨" if is_anomaly else ""
                logger.info(f"✓ {city_name} [{'+'.join(sources)}] → fact_measures (⭐ modèle en étoile){anomaly_flag}")
                return True
            else:
                logger.error(f"✗ Échec insertion {city_name}")
                return False
            
        except Exception as e:
            logger.error(f"Erreur transformation combinée: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self, batch_size: int = 100) -> dict:
        """Traite les données non traitées du Data Lake en combinant météo + AQI"""
        start_time = time.time()
        logger.info("="*60)
        logger.info(f"TRANSFORM COMBINÉ → BDD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        # Récupérer les données non traitées
        unprocessed_data = self.data_lake_service.get_unprocessed_data(limit=batch_size)
        
        if not unprocessed_data:
            logger.info("Aucune donnée à traiter")
            return {'success': 0, 'errors': 0, 'total': 0, 'duration': 0}
        
        logger.info(f"{len(unprocessed_data)} entrées à traiter")
        
        # Grouper par (city_id, timestamp) + dédoublonnage source/heure
        grouped, discarded_ids = self.group_by_city_and_time(unprocessed_data)
        logger.info(f"{len(grouped)} mesures combinées à créer ({len(discarded_ids)} doublons source/heure écartés)")
        
        success_count = 0
        processed_entries = 0
        
        for key, data in grouped.items():
            weather = data['weather']
            aqi = data['aqi']
            
            if self.transform_and_load_combined(weather, aqi):
                success_count += 1
                if weather: processed_entries += 1
                if aqi: processed_entries += 1

        # Marquer comme traitées les entrées dédoublonnées non retenues.
        discarded_marked = 0
        for lake_id in discarded_ids:
            if self.data_lake_service.mark_as_processed(lake_id):
                discarded_marked += 1

        if discarded_marked:
            logger.info(f"{discarded_marked} entrées dupliquées marquées comme traitées")
        
        # Stats
        duration = time.time() - start_time
        error_count = len(grouped) - success_count
        stats = {
            'success': success_count,
            'errors': error_count,
            'total': len(grouped),
            'processed_entries': processed_entries,
            'discarded_duplicates': discarded_marked,
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
        logger.info(f"Transformation terminée - {success_count} measures combinées ({processed_entries} entrées) - {duration:.2f}s")
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
