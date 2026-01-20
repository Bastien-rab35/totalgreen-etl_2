"""Test des connexions APIs et base de données"""
import sys
import logging
from config import config
from services import WeatherService, AirQualityService, DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_weather_api():
    """Test OpenWeather API"""
    logger.info("Test OpenWeather...")
    try:
        service = WeatherService(config.OPENWEATHER_API_KEY, config.OPENWEATHER_BASE_URL)
        data = service.fetch_weather_data("Paris")
        
        if data:
            logger.info(f"✓ OpenWeather OK - {data.get('parsed', {}).get('temp')}°C à Paris")
            return True
        else:
            logger.error("✗ OpenWeather échec")
            return False
    except Exception as e:
        logger.error(f"✗ OpenWeather erreur: {e}")
        return False

def test_air_quality_api():
    """Test AQICN API"""
    logger.info("Test AQICN...")
    try:
        service = AirQualityService(config.AQICN_API_KEY, config.AQICN_BASE_URL)
        data = service.fetch_air_quality_data("Paris")
        
        if data:
            logger.info(f"✓ AQICN OK - AQI {data.get('parsed', {}).get('aqi_index')} à Paris")
            return True
        else:
            logger.error("✗ AQICN échec")
            return False
    except Exception as e:
        logger.error(f"✗ AQICN erreur: {e}")
        return False

def test_database():
    """Test Supabase"""
    logger.info("Test Supabase...")
    try:
        service = DatabaseService(config.SUPABASE_URL, config.SUPABASE_KEY)
        cities = service.get_all_cities()
        
        logger.info(f"✓ Supabase OK - {len(cities)} villes")
        if len(cities) == 0:
            logger.warning("⚠ Aucune ville - Exécutez insert_cities.sql")
        return True
    except Exception as e:
        logger.error(f"✗ Supabase erreur: {e}")
        return False

def test_quotas():
    """Estime les quotas API"""
    logger.info("\nQuotas:")
    calls_per_day = 10 * 24  # 10 villes × 24h
    limit = 1000
    
    logger.info(f"  OpenWeather: {calls_per_day}/{limit} appels/jour ({(calls_per_day/limit)*100:.1f}%)")
    
    if calls_per_day < limit:
        logger.info("  ✓ Quota respecté")
        return True
    else:
        logger.error("  ✗ Quota dépassé!")
        return False

def main():
    """Exécute tous les tests"""
    logger.info("="*60)
    logger.info("TESTS DE CONNEXION - TotalGreen")
    logger.info("="*60)
    
    results = []
    
    # Config
    logger.info("\nValidation config...")
    try:
        config.validate()
        logger.info("✓ Config OK")
        results.append(True)
    except Exception as e:
        logger.error(f"✗ Config: {e}")
        return 1
    
    # Tests
    results.append(test_weather_api())
    results.append(test_air_quality_api())
    results.append(test_database())
    results.append(test_quotas())
    
    # Résumé
    logger.info("\n" + "="*60)
    if all(results):
        logger.info("✓ TOUS LES TESTS PASSÉS")
        logger.info("="*60)
        return 0
    else:
        logger.error("✗ CERTAINS TESTS ÉCHOUÉS")
        logger.info("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
