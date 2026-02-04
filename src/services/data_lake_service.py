"""
Service de gestion du Data Lake (stockage JSONB)
Stockage des données brutes avant transformation
"""
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DataLakeService:
    """Service de gestion du Data Lake - Stockage JSONB des données brutes"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialise la connexion à Supabase pour le Data Lake
        
        Args:
            supabase_url: URL du projet Supabase
            supabase_key: Clé d'API de service
        """
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("Connexion au Data Lake établie")
        except Exception as e:
            logger.error(f"Erreur de connexion au Data Lake: {e}")
            raise
    
    def store_raw_data(self, city_id: int, city_name: str, source: str, 
                       raw_data: Dict, collected_at: Optional[datetime] = None) -> Optional[int]:
        """Stocke les données brutes JSON dans le data lake"""
        try:
            # Utilise le timestamp de l'API si fourni, sinon le moment actuel
            timestamp = collected_at if collected_at else datetime.utcnow()
            
            entry = {
                'city_id': city_id,
                'city_name': city_name,
                'source': source,
                'raw_data': raw_data,
                'collected_at': timestamp.isoformat(),
                'processed': False
            }
            
            response = self.client.table('raw_data_lake').insert(entry).execute()
            
            if response.data:
                lake_id = response.data[0]['id']
                logger.info(f"Data lake: {source} - {city_name} (ID: {lake_id})")
                return lake_id
            return None
                
        except Exception as e:
            logger.error(f"Erreur data lake ({source} - {city_name}): {e}")
            return None
    
    def mark_as_processed(self, lake_id: int) -> bool:
        """Marque une entrée comme traitée"""
        try:
            update_data = {
                'processed': True,
                'processed_at': datetime.utcnow().isoformat()
            }
            self.client.table('raw_data_lake').update(update_data).eq('id', lake_id).execute()
            logger.info(f"Data lake {lake_id} marqué comme traité")
            return True
        except Exception as e:
            logger.error(f"Erreur update data lake (ID {lake_id}): {e}")
            return False
    
    def get_unprocessed_data(self, limit: int = 100) -> list:
        """
        Récupère les données non traitées du data lake
        
        Args:
            limit: Nombre maximum d'enregistrements à récupérer
            
        Returns:
            Liste des enregistrements non traités
        """
        try:
            response = (self.client.table('raw_data_lake')
                       .select('*')
                       .eq('processed', False)
                       .order('collected_at', desc=False)
                       .limit(limit)
                       .execute())
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données non traitées: {e}")
            return []
    
    def get_raw_data_by_city(self, city_id: int, limit: int = 10) -> Dict:
        """
        Récupère les dernières données brutes pour une ville
        
        Args:
            city_id: ID de la ville
            limit: Nombre de résultats par source
            
        Returns:
            Dictionnaire avec les données par source
        """
        try:
            # OpenWeather
            weather_response = (self.client.table('raw_data_lake')
                               .select('*')
                               .eq('city_id', city_id)
                               .eq('source', 'openweather')
                               .order('collected_at', desc=True)
                               .limit(limit)
                               .execute())
            
            # AQICN
            aqi_response = (self.client.table('raw_data_lake')
                           .select('*')
                           .eq('city_id', city_id)
                           .eq('source', 'aqicn')
                           .order('collected_at', desc=True)
                           .limit(limit)
                           .execute())
            
            return {
                'openweather': weather_response.data,
                'aqicn': aqi_response.data
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données brutes: {e}")
            return {'openweather': [], 'aqicn': []}
    
    def export_to_json_file(self, city_name: str, output_dir: str = "data/lake") -> bool:
        """
        Exporte les données brutes d'une ville vers un fichier JSON
        
        Args:
            city_name: Nom de la ville
            output_dir: Répertoire de sortie
            
        Returns:
            True si succès, False sinon
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            # Récupérer les données
            response = (self.client.table('raw_data_lake')
                       .select('*')
                       .eq('city_name', city_name)
                       .order('collected_at', desc=True)
                       .execute())
            
            if response.data:
                filename = f"{output_dir}/{city_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(response.data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Données exportées vers {filename}")
                return True
            else:
                logger.warning(f"Aucune donnée à exporter pour {city_name}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'export JSON: {e}")
            return False
