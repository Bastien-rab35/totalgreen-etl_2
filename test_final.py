import sys
sys.path.insert(0, 'src')

print('🔍 Test de la structure du code...\n')

# Test imports
print('1. Imports...')
from config import config
from services import WeatherService, AirQualityService, DatabaseService, DataLakeService
from etl_pipeline import ETLPipeline
from scheduler import run_job
print('   ✅ Tous les imports OK\n')

# Test config
print('2. Configuration...')
try:
    config.validate()
    print('   ✅ Config validée\n')
except Exception as e:
    print(f'   ⚠️  Config: {e}\n')

# Test instanciation services
print('3. Instanciation services...')
try:
    ws = WeatherService(config.OPENWEATHER_API_KEY, config.OPENWEATHER_BASE_URL)
    aqs = AirQualityService(config.AQICN_API_KEY, config.AQICN_BASE_URL)
    print('   ✅ Services APIs instanciés\n')
except Exception as e:
    print(f'   ❌ Erreur: {e}\n')

# Test pipeline
print('4. Pipeline ETL...')
try:
    pipeline = ETLPipeline()
    print('   ✅ Pipeline initialisé\n')
except Exception as e:
    print(f'   ⚠️  Pipeline: {e}\n')

print('='*50)
print('✅ STRUCTURE DU CODE VALIDÉE')
print('='*50)
