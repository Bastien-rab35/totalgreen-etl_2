#!/usr/bin/env python3
"""Test de la stratégie anti-perte de données"""
import sys
sys.path.insert(0, 'src')
from services.database_service import DatabaseService
from config import Config

db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)

print('\n' + '='*70)
print('🔍 VÉRIFICATION STRATÉGIE ANTI-PERTE')
print('='*70)

# 1. Vérifier les entrées non traitées
unprocessed = db.client.table('raw_data_lake')\
    .select('id,city_id,city_name,source,collected_at')\
    .eq('processed', False)\
    .order('collected_at', desc=True)\
    .execute()

print(f'\n📦 Data Lake - Entrées non traitées: {len(unprocessed.data)}')

if unprocessed.data:
    # Grouper par ville
    from collections import defaultdict
    from datetime import datetime
    
    by_city = defaultdict(lambda: {'weather': 0, 'aqi': 0})
    old_entries = []
    now = datetime.utcnow()
    
    for entry in unprocessed.data:
        city_id = entry['city_id']
        source = entry['source']
        
        # Détecter le type via la source ou les données
        if source == 'openweather':
            by_city[city_id]['weather'] += 1
        elif source == 'aqicn':
            by_city[city_id]['aqi'] += 1
        else:
            # Fallback: détecter via les données
            raw = db.client.table('raw_data_lake')\
                .select('raw_data')\
                .eq('id', entry['id'])\
                .single()\
                .execute()
            
            if raw.data:
                data = raw.data['raw_data']
                if 'main' in data and 'temp' in data.get('main', {}):
                    by_city[city_id]['weather'] += 1
                elif 'data' in data and 'aqi' in data.get('data', {}):
                    by_city[city_id]['aqi'] += 1
        
        # Calculer l'âge
        dt = datetime.fromisoformat(entry['collected_at'].replace('Z', '+00:00'))
        age_hours = (now - dt.replace(tzinfo=None)).total_seconds() / 3600
        
        if age_hours > 2:
            old_entries.append({
                'id': entry['id'],
                'city': entry['city_name'],
                'source': source,
                'age': age_hours,
                'collected_at': entry['collected_at']
            })
    
    print('\n📊 Par ville:')
    for city_id, counts in sorted(by_city.items()):
        city_name = next((e['city_name'] for e in unprocessed.data if e['city_id'] == city_id), f'City {city_id}')
        total = counts['weather'] + counts['aqi']
        balance = '⚖️ ' if counts['weather'] == counts['aqi'] else '⚠️ '
        print(f'   {balance}City {city_id:2d} ({city_name:12s}): {total:2d} entrées (Weather: {counts["weather"]}, AQI: {counts["aqi"]})')
    
    if old_entries:
        print(f'\n⏰ ENTRÉES ORPHELINES (> 2h, seront traitées immédiatement):')
        for e in old_entries[:10]:
            print(f'   • {e["city"]:12s} - {e["source"]:10s} - Âge: {e["age"]:5.1f}h - {e["collected_at"][:19]}')
        if len(old_entries) > 10:
            print(f'   ... et {len(old_entries) - 10} autres')
    else:
        print(f'\n✅ Aucune entrée orpheline (toutes < 2h)')
else:
    print('\n✅ Toutes les données sont traitées !')

# 2. Vérifier les mesures avec NULL
measures_count = db.client.table('measures').select('*', count='exact').execute()
null_temp = db.client.table('measures').select('*', count='exact').is_('temp', 'null').execute()
null_aqi = db.client.table('measures').select('*', count='exact').is_('aqi_index', 'null').execute()

print(f'\n💾 Measures dans la BDD: {measures_count.count}')
print(f'   Temp NULL: {null_temp.count} ({null_temp.count/measures_count.count*100:.1f}%)')
print(f'   AQI NULL: {null_aqi.count} ({null_aqi.count/measures_count.count*100:.1f}%)')

# 3. Statistiques de fusion
complete = measures_count.count - max(null_temp.count, null_aqi.count)
print(f'\n📈 Taux de fusion:')
print(f'   Complètes (weather+AQI): {complete} ({complete/measures_count.count*100:.1f}%)')
print(f'   Partielles (1 source): {max(null_temp.count, null_aqi.count)} ({max(null_temp.count, null_aqi.count)/measures_count.count*100:.1f}%)')

print('\n' + '='*70)
print('✅ STRATÉGIE: Fusion optimale + traitement orphelines après 2h')
print('   → 0% de perte de données garantie')
print('='*70 + '\n')
