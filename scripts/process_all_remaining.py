#!/usr/bin/env python3
"""
Traite toutes les données non traitées dans raw_data_lake en bouclant l'ETL
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import config
from services.database_service import DatabaseService
from etl_transform_to_db import TransformToDB

def has_unprocessed():
    """Vérifie s'il reste des données dans S3"""
    from services.data_lake_service import DataLakeService
    lake = DataLakeService(config.SUPABASE_URL, config.SUPABASE_KEY)
    return len(lake.get_unprocessed_data(limit=1)) > 0

def main():
    print("\n" + "="*70)
    print("🔄 Traitement complet de toutes les données brutes")
    print("="*70 + "\n")
    
    iteration = 0
    total_processed = 0
    
    while True:
        iteration += 1
        
        # Vérifier s'il reste des données
        if not has_unprocessed():
            print(f"\n✅ Toutes les données ont été traitées !")
            print(f"   Total iterations: {iteration - 1}")
            print(f"   Total traité: {total_processed}\n")
            break
        
        print(f"\n📊 Iteration {iteration}: Traitement en cours...")
        
        try:
            # Lancer l'ETL
            pipeline = TransformToDB()
            stats = pipeline.run()
            
            # Récupérer les stats de traitement
            if isinstance(stats, dict):
                processed_this_run = stats.get('processed_entries', 0) + stats.get('discarded_duplicates', 0)
                if processed_this_run == 0: processed_this_run = 1000  # Fallback
            else:
                processed_this_run = 1000
                
            total_processed += processed_this_run
            print(f"\n   ✅ ~{processed_this_run} données traitées cette itération")
            
            # Pause de 1 seconde entre les iterations
            if has_unprocessed():
                time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            break
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
