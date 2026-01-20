"""Scheduler - Exécute le pipeline ETL toutes les heures"""
import schedule
import time
import os
import logging
from datetime import datetime
from etl_pipeline import ETLPipeline
from config import config

os.makedirs('../logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_job():
    """Exécute le pipeline ETL"""
    logger.info(f"Job planifié - {datetime.now()}")
    try:
        pipeline = ETLPipeline()
        stats = pipeline.run()
        logger.info(f"Job terminé: {stats}")
    except Exception as e:
        logger.error(f"Erreur job: {e}")

def main():
    """Point d'entrée du scheduler"""
    logger.info("="*60)
    logger.info(f"Scheduler démarré - Intervalle: {config.COLLECTION_INTERVAL} min")
    logger.info("="*60)
    
    schedule.every(config.COLLECTION_INTERVAL).minutes.do(run_job)
    
    # Exécution immédiate
    run_job()
    
    logger.info("Scheduler actif (Ctrl+C pour arrêter)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler arrêté")

if __name__ == "__main__":
    main()
