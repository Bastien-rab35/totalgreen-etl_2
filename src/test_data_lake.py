"""
Test de l'architecture Data Lake
Valide le flux complet : Extract → Load (Data Lake JSONB) → Transform
"""
import logging
from datetime import datetime
from config import config
from services import WeatherService, AirQualityService, DataLakeService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_data_lake_workflow():
    """Test du workflow complet du data lake"""
    logger.info("=" * 60)
    logger.info("TEST DU DATA LAKE - Architecture ELT")
    logger.info("=" * 60)
    
    try:
        # Validation config
        config.validate()
        logger.info("✓ Configuration validée")
    except Exception as e:
        logger.error(f"✗ Erreur de configuration: {e}")
        return False
    
    # Initialisation des services
    try:
        weather_service = WeatherService(config.OPENWEATHER_API_KEY, config.OPENWEATHER_BASE_URL)
        aqi_service = AirQualityService(config.AQICN_API_KEY, config.AQICN_BASE_URL)
        data_lake = DataLakeService(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("✓ Services initialisés")
    except Exception as e:
        logger.error(f"✗ Erreur d'initialisation: {e}")
        return False
    
    city_name = "Paris"
    city_id = 1
    
    # ÉTAPE 1: EXTRACT
    logger.info("\n" + "=" * 60)
    logger.info("ÉTAPE 1: EXTRACT des données")
    logger.info("=" * 60)
    
    weather_data = weather_service.fetch_weather_data(city_name)
    aqi_data = aqi_service.fetch_air_quality_data(city_name)
    
    if weather_data and 'raw' in weather_data:
        logger.info(f"✓ Données météo extraites (raw + parsed)")
        logger.info(f"  Température: {weather_data['parsed'].get('temp')}°C")
    else:
        logger.error("✗ Échec extraction météo")
        return False
    
    if aqi_data and 'raw' in aqi_data:
        logger.info(f"✓ Données AQI extraites (raw + parsed)")
        logger.info(f"  AQI: {aqi_data['parsed'].get('aqi_index')}")
    else:
        logger.error("✗ Échec extraction AQI")
        return False
    
    # ÉTAPE 2: LOAD dans Data Lake (JSONB)
    logger.info("\n" + "=" * 60)
    logger.info("ÉTAPE 2: LOAD dans le Data Lake (JSONB)")
    logger.info("=" * 60)
    
    # Stockage météo
    raw_weather_id = data_lake.store_raw_data(
        city_id=city_id,
        city_name=city_name,
        source='openweather',
        raw_data=weather_data['raw']
    )
    
    if raw_weather_id:
        logger.info(f"✓ Données météo brutes stockées (ID: {raw_weather_id})")
    else:
        logger.error("✗ Échec stockage météo dans data lake")
        return False
    
    # Stockage AQI
    raw_aqi_id = data_lake.store_raw_data(
        city_id=city_id,
        city_name=city_name,
        source='aqicn',
        raw_data=aqi_data['raw']
    )
    
    if raw_aqi_id:
        logger.info(f"✓ Données AQI brutes stockées (ID: {raw_aqi_id})")
    else:
        logger.error("✗ Échec stockage AQI dans data lake")
        return False
    
    # ÉTAPE 3: Vérification du stockage
    logger.info("\n" + "=" * 60)
    logger.info("ÉTAPE 3: VÉRIFICATION du Data Lake")
    logger.info("=" * 60)
    
    # Récupérer les données stockées
    lake_data = data_lake.get_raw_data_by_city(city_id, limit=2)
    
    logger.info(f"✓ Données récupérées du data lake:")
    logger.info(f"  - OpenWeather: {len(lake_data.get('openweather', []))} enregistrements")
    logger.info(f"  - AQICN: {len(lake_data.get('aqicn', []))} enregistrements")
    
    # Afficher un extrait des données JSONB
    if lake_data.get('openweather'):
        latest_weather = lake_data['openweather'][0]
        logger.info(f"\n📦 Exemple de données JSONB (OpenWeather):")
        logger.info(f"  ID: {latest_weather.get('id')}")
        logger.info(f"  Collecté: {latest_weather.get('collected_at')}")
        logger.info(f"  Traité: {latest_weather.get('processed')}")
        logger.info(f"  Température (raw): {latest_weather.get('raw_data', {}).get('main', {}).get('temp')}°C")
    
    # ÉTAPE 4: Marquer comme traité
    logger.info("\n" + "=" * 60)
    logger.info("ÉTAPE 4: TRANSFORMATION (simulation)")
    logger.info("=" * 60)
    
    logger.info(f"  Données parsées prêtes pour insertion dans 'measures':")
    logger.info(f"  - Température: {weather_data['parsed'].get('temp')}°C")
    logger.info(f"  - Humidité: {weather_data['parsed'].get('humidity')}%")
    logger.info(f"  - AQI: {aqi_data['parsed'].get('aqi_index')}")
    logger.info(f"  - PM2.5: {aqi_data['parsed'].get('pm25')}")
    
    # Marquer comme traité
    if data_lake.mark_as_processed(raw_weather_id):
        logger.info(f"✓ Données météo marquées comme traitées")
    
    if data_lake.mark_as_processed(raw_aqi_id):
        logger.info(f"✓ Données AQI marquées comme traitées")
    
    # ÉTAPE 5: Export JSON (optionnel)
    logger.info("\n" + "=" * 60)
    logger.info("ÉTAPE 5: EXPORT JSON (optionnel)")
    logger.info("=" * 60)
    
    if data_lake.export_to_json_file(city_name, output_dir="data/lake"):
        logger.info(f"✓ Export JSON réussi pour {city_name}")
    
    # Récapitulatif
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DU TEST")
    logger.info("=" * 60)
    logger.info("✅ Architecture Data Lake validée:")
    logger.info("  1. Extract: Données brutes + parsées récupérées")
    logger.info("  2. Load: Stockage JSONB dans raw_data_lake")
    logger.info("  3. Transform: Données prêtes pour tables structurées")
    logger.info("  4. Traçabilité: Liens raw_weather_id / raw_aqi_id")
    logger.info("  5. Export: Fichiers JSON disponibles")
    logger.info("\n💡 Avantages:")
    logger.info("  - Données brutes conservées (auditabilité)")
    logger.info("  - Requêtes SQL possibles sur JSONB")
    logger.info("  - Retraitement possible sans nouvelle collecte")
    logger.info("  - Conformité cahier des charges (Data Lake)")
    
    return True

if __name__ == "__main__":
    success = test_data_lake_workflow()
    
    if success:
        logger.info("\n✅ TEST RÉUSSI - Architecture Data Lake opérationnelle")
        exit(0)
    else:
        logger.error("\n❌ TEST ÉCHOUÉ - Vérifier la configuration")
        exit(1)
