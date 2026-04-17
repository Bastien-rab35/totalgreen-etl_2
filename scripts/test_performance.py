#!/usr/bin/env python3
"""
Script de test des performances réelles du pipeline (Refactorisé niveau Master Data Engineering)
Mesure la latence API, le throughput d'insertion DB et la taille du Data Lake.
"""
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config, setup_logging
from src.services.database_service import DatabaseService

# Logging configuration locally for tests
setup_logging(logging.ERROR)
logger = logging.getLogger("PerfTest")

def measure_time(func):
    """Décorateur pour mesurer le temps d'exécution d'une fonction."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        return result, duration
    return wrapper

class PerformanceTester:
    def __init__(self):
        self.db = DatabaseService(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.metrics = {}

    @measure_time
    def test_database_latency(self) -> dict:
        """Teste la latence de base de la connexion Supabase."""
        try:
            self.db.client.table("dim_city").select("city_id", count="exact").limit(1).execute()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @measure_time
    def test_olap_query_performance(self) -> dict:
        """Teste une requête analytique complexe (JOIN) sur les faits."""
        try:
            # Fact Measures (Ancien format)
            response = self.db.client.table("fact_measures").select("*, dim_city(*), dim_date(*)").limit(100).execute()
            return {"status": "success", "rows": len(response.data)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @measure_time
    def test_tomtom_hubeau_selects(self) -> dict:
        """Teste les lectures sur le nouveau modèle TomTom/HubEau."""
        try:
            res_flow = self.db.client.table("fact_traffic_flow_hourly").select("*").limit(100).execute()
            return {"status": "success", "flow_rows": len(res_flow.data)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def estimate_storage_footprint(self) -> dict:
        """Estime la volumétrie des tables principales."""
        try:
            lake_res = self.db.client.table("raw_data_lake").select("id", count="exact").limit(1).execute()
            lake_count = lake_res.count or 0

            fact_flow_res = self.db.client.table("fact_traffic_flow_hourly").select("traffic_flow_id", count="exact").limit(1).execute()
            flow_count = fact_flow_res.count or 0

            measure_res = self.db.client.table("fact_measures").select("measure_id", count="exact").limit(1).execute()
            measure_count = measure_res.count or 0

            # Calcul des tailles (~2000 bytes pour JSON, ~200 bytes pour records normaux)
            lake_mb = (lake_count * 2000) / (1024 * 1024)
            flow_mb = (flow_count * 200) / (1024 * 1024)
            measure_mb = (measure_count * 200) / (1024 * 1024)

            return {
                "lake_count": lake_count,
                "fact_traffic_flow_count": flow_count,
                "fact_measures_count": measure_count,
                "lake_mb": lake_mb,
                "model_mb": flow_mb + measure_mb,
                "total_mb": lake_mb + flow_mb + measure_mb
            }
        except Exception as e:
            logger.error(f"Erreur d'estimation du stockage : {e}")
            return {}

    def run_all(self):
        print("=" * 60)
        print("🚀 TEST DE PERFORMANCES DWH & DATA LAKE (MSPR2)")
        print("=" * 60)
        
        # 1. Tests de latence réseau / base de données
        print("\n1️⃣ LATENCE RÉSEAU & DATABASE READS")
        print("-" * 60)
        res_lat, t_lat = self.test_database_latency()
        print(f"[{res_lat['status']}] Ping Supabase (dim_city)     : {t_lat*1000:.2f} ms")
        
        res_olap, t_olap = self.test_olap_query_performance()
        print(f"[{res_olap['status']}] Requête OLAP JSON (Join x3): {t_olap*1000:.2f} ms (Lignes: {res_olap.get('rows', 0)})")

        res_tomtom, t_tomtom = self.test_tomtom_hubeau_selects()
        print(f"[{res_tomtom['status']}] Lecture TomTom / HubEau      : {t_tomtom*1000:.2f} ms (Lignes: {res_tomtom.get('flow_rows', 0)})")

        # 2. Métriques de volumétrie
        print("\n2️⃣ VOLUMÉTRIE & CROISSANCE")
        print("-" * 60)
        stats = self.estimate_storage_footprint()
        if stats:
            print(f"📦 Raw Data Lake                : {stats.get('lake_count'):,} lignes ({stats.get('lake_mb'):.2f} MB)")
            print(f"📊 Fact Traffic Flow (Horaires) : {stats.get('fact_traffic_flow_count'):,} lignes")
            print(f"📊 Fact Measures                : {stats.get('fact_measures_count'):,} lignes")
            print(f"💾 Poids Analystique total      : ~ {stats.get('model_mb'):.2f} MB")
            print(f"💾 Empreinte Poids (Total)      : ~ {stats.get('total_mb'):.2f} MB")
            
            # Calcul croisé journalier projeté
            daily_ingestion = 100 * 24 # 100 villes/points par heure * 24h
            print(f"📈 Projection insertion Lake/J  : {daily_ingestion * 3:,} records/jour (Météo/AQI/Trafic)")
            
            monthly_growth = (daily_ingestion * 3 * 30 * 2000) / (1024*1024)
            print(f"📈 Croissance Data Lake estimée : +{monthly_growth:.2f} MB / Mois")

        print("\n" + "=" * 60)
        print("✅ TEST TERMINÉ")
        print("=" * 60)

if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run_all()
