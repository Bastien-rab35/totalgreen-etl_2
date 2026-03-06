#!/usr/bin/env python3
"""
Script de test des performances réelles du pipeline
"""
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.services.database_service import DatabaseService

def test_performance():
    print("="*60)
    print("TEST PERFORMANCES PIPELINE ETL")
    print("="*60)
    
    db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # 1. Compter les mesures totales
    print("\n1. MÉTRIQUES DONNÉES")
    print("-" * 60)
    
    try:
        # Total mesures
        response = db.client.table('fact_measures').select('*', count='exact').execute()
        total_measures = response.count
        print(f"Total mesures en BDD : {total_measures:,}")
        
        # Mesures par jour (moyenne sur 7 derniers jours)
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        
        response_week = db.client.table('fact_measures').select('*', count='exact').gte('created_at', seven_days_ago.isoformat()).execute()
        measures_week = response_week.count
        avg_per_day = measures_week / 7 if measures_week > 0 else 0
        print(f"Mesures (7 derniers jours) : {measures_week}")
        print(f"Moyenne par jour : {avg_per_day:.0f}")
        
        # Vérifier les doublons
        response_all = db.client.table('fact_measures').select('city_id, captured_at').execute()
        data = response_all.data
        
        seen = set()
        duplicates = 0
        for measure in data:
            key = (measure.get('city_id'), measure.get('captured_at'))
            if key in seen:
                duplicates += 1
            seen.add(key)
        
        print(f"Doublons dans fact_measures : {duplicates}")
        
    except Exception as e:
        print(f"Erreur : {e}")
    
    # 2. Taille de stockage
    print("\n2. STOCKAGE")
    print("-" * 60)
    
    try:
        # Taille Data Lake
        response_lake = db.client.table('raw_data_lake').select('raw_data', count='exact').execute()
        lake_count = response_lake.count
        
        # Estimer la taille moyenne d'une entrée JSONB
        if response_lake.data:
            import json
            sample_size = min(100, len(response_lake.data))
            total_bytes = sum(len(json.dumps(d['raw_data'])) for d in response_lake.data[:sample_size] if d.get('raw_data'))
            avg_bytes_per_entry = total_bytes / sample_size if sample_size > 0 else 0
            total_lake_mb = (avg_bytes_per_entry * lake_count) / (1024 * 1024)
            print(f"Data Lake : {lake_count:,} entrées")
            print(f"Taille estimée Data Lake : {total_lake_mb:.2f} MB")
        
        # Estimer taille fact_measures (approximation)
        # En moyenne : ~50 colonnes * 8 bytes (numeric) = 400 bytes/mesure
        fact_size_mb = (total_measures * 400) / (1024 * 1024)
        print(f"Taille estimée fact_measures : {fact_size_mb:.2f} MB")
        
        # Total
        total_mb = total_lake_mb + fact_size_mb
        print(f"Stockage total estimé : {total_mb:.2f} MB")
        
        # Par jour
        if avg_per_day > 0:
            # Chaque mesure = 1 entrée lake + 1 entrée fact
            storage_per_day = ((avg_bytes_per_entry + 400) * avg_per_day) / 1024  # en KB
            print(f"Stockage par jour : {storage_per_day:.0f} KB")
        
    except Exception as e:
        print(f"Erreur stockage : {e}")
    
    # 3. Test de temps d'exécution
    print("\n3. TEMPS D'EXÉCUTION")
    print("-" * 60)
    
    # Test requête simple
    start = time.time()
    db.client.table('fact_measures').select('*').limit(100).execute()
    query_time = (time.time() - start) * 1000
    print(f"SELECT 100 mesures : {query_time:.0f} ms")
    
    # Test requête avec JOIN (simulation OLAP)
    start = time.time()
    db.client.table('fact_measures').select('*, dim_city(*), dim_time(*)').limit(50).execute()
    join_time = (time.time() - start) * 1000
    print(f"SELECT 50 mesures + JOIN : {join_time:.0f} ms")
    
    # Test insertion
    print("\nNote : Les temps Extract (20s) et Transform (3s)")
    print("       sont basés sur les logs GitHub Actions")
    
    print("\n" + "="*60)
    print("TEST TERMINÉ")
    print("="*60)

if __name__ == "__main__":
    test_performance()
