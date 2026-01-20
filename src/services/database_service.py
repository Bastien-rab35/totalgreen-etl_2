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
            self.client: Client = create_client(supabase_url, supabase_key)
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
