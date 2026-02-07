#!/usr/bin/env python3
"""Vérification de l'état actuel de la BDD"""
import sys
sys.path.insert(0, 'src')
from config import Config
from services.database_service import DatabaseService

db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)

print('='*70)
print('📊 ÉTAT ACTUEL DE LA BDD')
print('='*70)

# Statistiques globales
total_lake = db.client.table('raw_data_lake').select('*', count='exact').execute()
total_measures = db.client.table('measures').select('*', count='exact').execute()
processed = db.client.table('raw_data_lake').select('*', count='exact').eq('processed', True).execute()
unprocessed = db.client.table('raw_data_lake').select('*', count='exact').eq('processed', False).execute()

print(f'\n📦 Data Lake:')
print(f'   Total: {total_lake.count}')
print(f'   Processed: {processed.count}')
print(f'   Non-processed: {unprocessed.count}')

print(f'\n📊 Measures:')
print(f'   Total: {total_measures.count}')

# Dernières measures insérées
print(f'\n🆕 Dernières 10 measures:')
latest = db.client.table('measures').select('id, city_id, captured_at, temp, aqi_index, created_at').order('id', desc=True).limit(10).execute()
for m in latest.data:
    print(f'   ID {m["id"]:5d} | City {m["city_id"]:2d} | captured_at: {m["captured_at"][:19]} | temp: {str(m.get("temp"))[:5]:>5s}°C | AQI: {str(m.get("aqi_index"))[:4]:>4s} | created: {m["created_at"][:19]}')

# Statistiques NULL
null_temp = db.client.table('measures').select('*', count='exact').is_('temp', 'null').execute()
null_aqi = db.client.table('measures').select('*', count='exact').is_('aqi_index', 'null').execute()

print(f'\n📈 Qualité des données:')
print(f'   Temp NULL: {null_temp.count}/{total_measures.count} ({null_temp.count/total_measures.count*100:.1f}%)')
print(f'   AQI NULL: {null_aqi.count}/{total_measures.count} ({null_aqi.count/total_measures.count*100:.1f}%)')

print('\n' + '='*70)
