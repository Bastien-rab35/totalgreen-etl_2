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

def count_unprocessed():
    """Compte les données non traitées"""
    db = DatabaseService(config.SUPABASE_URL, config.SUPABASE_KEY)
    result = db.client.table('raw_data_lake').select('*', count='exact').eq('processed', False).execute()
    return result.count

def main():
    print("\n" + "="*70)
    print("🔄 Traitement complet de toutes les données brutes")
    print("="*70 + "\n")
    
    iteration = 0
    total_processed = 0
    
    while True:
        iteration += 1
        
        # Compter les données non traitées
        unprocessed = count_unprocessed()
        
        if unprocessed == 0:
            print(f"\n✅ Toutes les données ont été traitées !")
            print(f"   Total iterations: {iteration - 1}")
            print(f"   Total traité: {total_processed}\n")
            break
        
        print(f"\n📊 Iteration {iteration}: {unprocessed} données non traitées")
        
        try:
            # Lancer l'ETL
            pipeline = TransformToDB()
            stats = pipeline.run()
            
            # Compter combien ont été traités
            unprocessed_after = count_unprocessed()
            processed_this_run = unprocessed - unprocessed_after
            total_processed += processed_this_run
            
            print(f"\n   ✅ {processed_this_run} données traitées cette itération")
            print(f"   📦 Restant: {unprocessed_after}")
            
            # Pause de 1 seconde entre les iterations
            if unprocessed_after > 0:
                time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            break
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
