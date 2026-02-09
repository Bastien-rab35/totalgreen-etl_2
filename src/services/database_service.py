"""
Service de gestion de la base de données Supabase
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service de gestion de la persistance des données"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialise la connexion à Supabase
        
        Args:
            supabase_url: URL du projet Supabase
            supabase_key: Clé d'API de service
        """
        try:
            # Compatibilité avec supabase-py 2.x
            self.client: Client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_key
            )
            logger.info("Connexion à Supabase établie")
        except Exception as e:
            logger.error(f"Erreur de connexion à Supabase: {e}")
            raise
    
    def get_all_cities(self) -> List[Dict]:
        """
        Récupère toutes les villes du référentiel
        
        Returns:
            Liste des villes avec leurs coordonnées
        """
        try:
            response = self.client.table('cities').select('*').execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des villes: {e}")
            return []
    
    def insert_measure(self, city_id: int, weather_data: Dict, aqi_data: Dict, 
                      raw_weather_id: int = None, raw_aqi_id: int = None) -> bool:
        """
        Insère une nouvelle mesure dans la base de données
        
        Args:
            city_id: ID de la ville
            weather_data: Données météorologiques
            raw_weather_id: ID dans le data lake (données météo brutes)
            raw_aqi_id: ID dans le data lake (données AQI brutes)
            
        Returns:
            True si succès, False sinon
        """
        try:
            measure = {
                'city_id': city_id,
                'raw_weather_id': raw_weather_id,
                'raw_aqi_id': raw_aqi_id,
                'captured_at': datetime.utcnow().isoformat(),
                **weather_data,
                **aqi_data
            }
            
            # Nettoyage des valeurs None
            measure = {k: v for k, v in measure.items() if v is not None}
            
            response = self.client.table('measures').insert(measure).execute()
            logger.info(f"Mesure insérée pour city_id={city_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de la mesure: {e}")
            return False
    
    def log_etl_execution(self, status: str, source: str, city_id: Optional[int] = None, 
                          records_inserted: int = 0, error_message: Optional[str] = None,
                          duration: float = 0) -> None:
        """Enregistre l'exécution d'un job ETL"""
        try:
            log_entry = {
                'execution_time': datetime.utcnow().isoformat(),
                'status': status,
                'source': source,
                'city_id': city_id,
                'records_inserted': records_inserted,
                'error_message': error_message,
                'execution_duration_seconds': duration
            }
            self.client.table('etl_logs').insert(log_entry).execute()
            logger.info(f"ETL log: {status} - {source}")
        except Exception as e:
            logger.error(f"Erreur log ETL: {e}")
    
    def insert_measure_direct(self, measure: Dict) -> bool:
        """
        Insère directement une mesure (utilisé par le pipeline de transformation)
        ANCIENNE VERSION: insère dans measures (normalisé)
        
        Args:
            measure: Dictionnaire contenant les données de la mesure
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Nettoyage des valeurs None
            measure = {k: v for k, v in measure.items() if v is not None}
            
            response = self.client.table('measures').insert(measure).execute()
            logger.info(f"Mesure insérée pour city_id={measure.get('city_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de la mesure: {e}")
            return False
    
    def insert_into_star_schema(self, measure: Dict) -> bool:
        """
        Insère une mesure dans le modèle en étoile (fact_measures)
        
        Args:
            measure: Dictionnaire contenant:
                - city_id, captured_at
                - temp, feels_like, humidity, etc. (météo)
                - aqi_index, pm25, pm10, etc. (qualité air)
                - weather_id (pour lookup dim_weather_condition)
                - raw_weather_id, raw_aqi_id (traçabilité)
        
        Returns:
            True si succès, False sinon
        """
        try:
            from datetime import datetime
            
            # 1. Récupérer time_id depuis dim_time (arrondi à l'heure)
            captured_at = measure.get('captured_at')
            if captured_at:
                dt = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
                hour_truncated = dt.replace(minute=0, second=0, microsecond=0).isoformat()
                
                # Lookup time_id
                time_result = self.client.table('dim_time').select('time_id').eq('full_date', hour_truncated).limit(1).execute()
                time_id = time_result.data[0]['time_id'] if time_result.data else None
            else:
                time_id = None
            
            # 2. Récupérer weather_condition_id depuis dim_weather_condition
            weather_id = measure.get('weather_id')
            weather_condition_id = None
            if weather_id:
                weather_result = self.client.table('dim_weather_condition').select('weather_condition_id').eq('weather_id', weather_id).limit(1).execute()
                weather_condition_id = weather_result.data[0]['weather_condition_id'] if weather_result.data else None
            
            # 3. Calculer aqi_level_id (via fonction PostgreSQL)
            aqi_index = measure.get('aqi_index')
            aqi_level_id = None
            if aqi_index:
                # Utiliser la fonction get_aqi_level_id définie dans star_schema.sql
                aqi_result = self.client.rpc('get_aqi_level_id', {'aqi_value': aqi_index}).execute()
                aqi_level_id = aqi_result.data if aqi_result.data else None
            
            # 4. Construire l'enregistrement pour fact_measures
            fact_measure = {
                'time_id': time_id,
                'city_id': measure.get('city_id'),
                'weather_condition_id': weather_condition_id,
                'aqi_level_id': aqi_level_id,
                
                # Métriques météo
                'temperature': measure.get('temp'),
                'feels_like': measure.get('feels_like'),
                'pressure': measure.get('pressure'),
                'humidity': measure.get('humidity'),
                'wind_speed': measure.get('wind_speed'),
                'wind_deg': measure.get('wind_deg'),
                'wind_gust': measure.get('wind_gust'),
                'clouds': measure.get('clouds'),
                'visibility': measure.get('visibility'),
                'rain_1h': measure.get('rain_1h', 0),
                'snow_1h': measure.get('snow_1h', 0),
                
                # Métriques qualité air
                'aqi_index': aqi_index,
                'pm25': measure.get('pm25'),
                'pm10': measure.get('pm10'),
                'no2': measure.get('no2'),
                'o3': measure.get('o3'),
                'so2': measure.get('so2'),
                'co': measure.get('co'),
                
                # Traçabilité
                'raw_weather_id': measure.get('raw_weather_id'),
                'raw_aqi_id': measure.get('raw_aqi_id')
            }
            
            # Nettoyage des None
            fact_measure = {k: v for k, v in fact_measure.items() if v is not None}
            
            # 5. Insérer dans fact_measures
            response = self.client.table('fact_measures').insert(fact_measure).execute()
            logger.info(f"✓ Mesure insérée dans modèle en étoile - city_id={measure.get('city_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur insertion modèle en étoile: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_latest_measures(self, city_id: int, limit: int = 10) -> List[Dict]:
        """Récupère les dernières mesures"""
        try:
            response = (self.client.table('measures')
                       .select('*')
                       .eq('city_id', city_id)
                       .order('captured_at', desc=True)
                       .limit(limit)
                       .execute())
            return response.data
        except Exception as e:
            logger.error(f"Erreur récupération mesures: {e}")
            return []
