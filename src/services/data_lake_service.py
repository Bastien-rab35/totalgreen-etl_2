"""
Service de gestion du Data Lake - Stockage Objet (S3 Scaleway)
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List
import boto3
from botocore.config import Config as BotoConfig

try:
    from config import config
except ImportError:
    from src.config import config

logger = logging.getLogger(__name__)

class DataLakeService:
    """Service de gestion du Data Lake - Stockage Objet S3"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialise la connexion à Scaleway Object Storage (S3)
        (Les arguments supabase_* sont ignorés mais conservés pour rétrocompatibilité)
        """
        self.bucket_name = config.S3_BUCKET_NAME
        try:
            # Configuration S3 pour Scaleway
            boto_cfg = BotoConfig(region_name='fr-par', retries={'max_attempts': 3})
            self.s3_client = boto3.client(
                's3',
                endpoint_url=config.S3_ENDPOINT_URL,
                aws_access_key_id=config.S3_ACCESS_KEY,
                aws_secret_access_key=config.S3_SECRET_KEY,
                config=boto_cfg
            )
            logger.info(f"Connexion au Data Lake S3 établie (Bucket: {self.bucket_name})")
        except Exception as e:
            logger.error(f"Erreur connexion S3: {e}")
            raise
    
    def store_raw_data(self, city_id: int, city_name: str, source: str, 
                       raw_data: Dict, collected_at: Optional[datetime] = None) -> Optional[str]:
        """Stocke les données brutes JSON sous forme de fichier dans le bucket S3"""
        try:
            timestamp = collected_at if collected_at else datetime.now(timezone.utc)
            ts_str = timestamp.strftime('%Y%m%d_%H%M%S')
            uid = uuid.uuid4().hex[:8]
            
            # Key S3 = unprocessed/openweather/1_20260527_140000_abcd1234.json
            key = f"unprocessed/{source}/{city_id}_{ts_str}_{uid}.json"
            
            entry = {
                'city_id': city_id,
                'city_name': city_name,
                'source': source,
                'raw_data': raw_data,
                'collected_at': timestamp.isoformat(),
                'processed': False
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(entry, ensure_ascii=False).encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"Data lake S3: {source} - {city_name} (Key: {key})")
            return key
            
        except Exception as e:
            logger.error(f"Erreur upload S3 ({source} - {city_name}): {e}")
            return None
    
    def mark_as_processed(self, lake_id: int) -> bool:
        """Déplace le fichier de unprocessed/ vers processed/"""
        lake_key = str(lake_id)
        if not lake_key.startswith('unprocessed/'):
            return True
            
        new_key = lake_key.replace('unprocessed/', 'processed/', 1)
        try:
            # Copier vers le nouveau dossier
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': lake_key},
                Key=new_key
            )
            # Supprimer l'original
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=lake_key
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mark_as_processed S3 ({lake_key}): {e}")
            return False

    def mark_as_processed_batch(self, lake_ids: List[int], batch_size: int = 100) -> int:
        """Marque en batch une liste de clés S3 comme traitées."""
        if not lake_ids:
            return 0
        processed_count = 0
        for lake_id in lake_ids:
            if self.mark_as_processed(lake_id):
                processed_count += 1
        return processed_count
    
    def get_unprocessed_data(self, limit: int = 100) -> list:
        """Récupère les données non traitées depuis le dossier unprocessed/ du S3"""
        try:
            unprocessed = []
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="unprocessed/",
                MaxKeys=limit
            )
            
            if 'Contents' not in response:
                return unprocessed
                
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('/'):
                    continue
                    
                res = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                content = res['Body'].read().decode('utf-8')
                data = json.loads(content)
                
                # Injecte la clé S3 comme ID pour le pipeline
                data['id'] = key
                unprocessed.append(data)
                
            return unprocessed
        except Exception as e:
            logger.error(f"Erreur lors de la récupération depuis S3: {e}")
            return []

    def get_raw_data_by_city(self, city_id: int, limit: int = 10) -> Dict:
        """Obsolète avec S3 - Retourne une structure vide pour compatibilité"""
        return {'openweather': [], 'aqicn': []}
    
    def export_to_json_file(self, city_name: str, output_dir: str = "data/lake") -> bool:
        """Obsolète avec S3 - Retourne False pour compatibilité"""
        return False
