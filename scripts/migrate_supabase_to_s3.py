#!/usr/bin/env python3
"""
Script de migration one-shot pour transférer les données de la table
raw_data_lake (Supabase) vers le Data Lake S3 (Scaleway Object Storage).
"""

import sys
import argparse
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.services.database_service import DatabaseService
import boto3
from botocore.config import Config as BotoConfig

# --- S3 Uploader Class (copié de DataLakeService pour l'autonomie du script) ---

class S3Uploader:
    def __init__(self):
        self.bucket_name = config.S3_BUCKET_NAME
        try:
            boto_cfg = BotoConfig(region_name='fr-par', retries={'max_attempts': 3})
            self.s3_client = boto3.client(
                's3',
                endpoint_url=config.S3_ENDPOINT_URL,
                aws_access_key_id=config.S3_ACCESS_KEY,
                aws_secret_access_key=config.S3_SECRET_KEY,
                config=boto_cfg
            )
            print(f"✅ Connexion à S3 établie (Bucket: {self.bucket_name})")
        except Exception as e:
            print(f"❌ Erreur de connexion à S3: {e}")
            raise

    def upload_record(self, record: dict, dry_run: bool = False) -> bool:
        """Construit et upload un fichier JSON sur S3 à partir d'un record Supabase."""
        try:
            # Recréer la structure de fichier attendue par le nouveau DataLakeService
            timestamp_str = record.get('collected_at')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now(timezone.utc)

            ts_str = timestamp.strftime('%Y%m%d_%H%M%S')
            uid = uuid.uuid4().hex[:8]
            city_id = record.get('city_id', 0)
            source = record.get('source', 'unknown')
            
            # Placer dans 'processed' ou 'unprocessed' selon l'état dans Supabase
            status_folder = 'processed' if record.get('processed') else 'unprocessed'
            
            key = f"{status_folder}/{source}/{city_id}_{ts_str}_{uid}.json"

            if dry_run:
                print(f"   [DRY-RUN] Créerait le fichier S3 : {key}")
                return True

            # Le corps du fichier est l'enregistrement Supabase lui-même
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(record, ensure_ascii=False, default=str).encode('utf-8'),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"   ❌ Erreur lors de l'upload S3 pour l'ID {record.get('id')}: {e}")
            return False

# --- Main Migration Logic ---

def run_migration(dry_run: bool, batch_size: int = 500):
    """Exécute la migration complète."""
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE LA MIGRATION : Supabase `raw_data_lake` → Scaleway S3")
    print("="*70)

    if dry_run:
        print("\n⚠️  MODE DRY-RUN - Aucun fichier ne sera uploadé sur S3.")

    try:
        config.validate()
        db = DatabaseService(config.SUPABASE_URL, config.SUPABASE_KEY)
        s3_uploader = S3Uploader()
        print("✅ Connexion à Supabase établie.")
    except Exception as e:
        print(f"❌ Erreur d'initialisation : {e}")
        return

    # Boucler par pagination
    migrated_count = 0
    error_count = 0
    last_id = 0
    
    while True:
        print(f"\n🚚 Traitement du lot de {batch_size} lignes (à partir de l'ID > {last_id})...")

        try:
            batch_res = db.client.table('raw_data_lake').select('*').gt('id', last_id).order('id').limit(batch_size).execute()
            
            if not batch_res.data:
                print("   - Fin des données.")
                break

            batch_record_count = len(batch_res.data)
            
            # Utiliser un ThreadPoolExecutor pour uploader en parallèle
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_record = {executor.submit(s3_uploader.upload_record, record, dry_run): record for record in batch_res.data}
                
                for future in as_completed(future_to_record):
                    record_id = future_to_record[future].get('id')
                    try:
                        if future.result():
                            migrated_count += 1
                        else:
                            error_count += 1
                    except Exception as exc:
                        print(f"   ❌ Erreur thread pour ID {record_id}: {exc}")
                        error_count += 1
            
            print(f"   - Lot de {batch_record_count} lignes traité. Total migré : {migrated_count}, Erreurs : {error_count}")
            
            last_id = batch_res.data[-1]['id']

            if batch_record_count < batch_size:
                print("   - Dernier lot traité.")
                break
        except Exception as e:
            print(f"   ❌ Erreur critique lors de la récupération du lot : {e}")
            break
    
    print("\n" + "="*70)
    print("🏁 MIGRATION TERMINÉE")
    print("="*70)
    print(f"\n- Lignes migrées avec succès : {migrated_count}")
    print(f"- Erreurs rencontrées : {error_count}")

    if not dry_run and error_count == 0:
        print("\n\n⚠️ ACTION MANUELLE REQUISE ⚠️")
        print("La migration semble réussie. Pour libérer l'espace sur Supabase, vous devez maintenant supprimer les données de la table `raw_data_lake`.")
        print("Copiez-collez la commande suivante dans l'éditeur SQL de Supabase après avoir vérifié que les fichiers sont bien présents sur Scaleway S3 :")
        print("\nTRUNCATE public.raw_data_lake;")
        print("\nCette action est IRRÉVERSIBLE et videra complètement la table.")
    elif dry_run:
        print("\nCeci était une simulation. Relancez le script sans `--dry-run` pour effectuer la migration réelle.")
    else:
        print("\nDes erreurs ont été rencontrées. Veuillez vérifier les logs avant de procéder au nettoyage manuel de la base de données.")


def main():
    parser = argparse.ArgumentParser(
        description="Migre les données de la table Supabase `raw_data_lake` vers Scaleway S3."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Mode simulation pour voir ce qui serait fait sans rien uploader."
    )
    args = parser.parse_args()

    run_migration(dry_run=args.dry_run)


if __name__ == '__main__':
    main()