#!/usr/bin/env python3
"""Rapport complet après la nuit"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Data Lake
total = client.table('raw_data_lake').select('id', count='exact').execute()
processed = client.table('raw_data_lake').select('id', count='exact').eq('processed', True).execute()
unprocessed = total.count - processed.count

# Mesures BDD
measures = client.table('measures').select('id', count='exact').execute()

# Logs transform
transform_logs = client.table('etl_logs').select('*').eq('source', 'transform').order('execution_time', desc=True).limit(5).execute()

# Logs extract
extract_logs = client.table('etl_logs').select('*').eq('source', 'extract').order('execution_time', desc=True).limit(15).execute()

print('\n' + '='*60)
print('📊 RAPPORT ETL - Après la nuit')
print('='*60)

print(f'\n📦 DATA LAKE (raw_data_lake):')
print(f'   Total: {total.count} entrées JSONB')
print(f'   ✅ Traités: {processed.count}')
print(f'   ⏳ En attente: {unprocessed}')

print(f'\n💾 MESURES (BDD normalisée): {measures.count} entrées')

print('\n🔄 Dernières transformations (Data Lake → BDD):')
if transform_logs.data:
    for log in transform_logs.data:
        status = '✅' if log['status'] == 'success' else '❌'
        print(f'   {status} {log["execution_time"][:19]} - {log["records_inserted"]} insérés ({log["execution_duration_seconds"]:.1f}s)')
else:
    print('   ⚠️ Aucune transformation trouvée')

print(f'\n📥 Dernières extractions (API → Data Lake):')
success_count = sum(1 for l in extract_logs.data if l['status'] == 'success')
total_collected = sum(l['records_inserted'] for l in extract_logs.data)
print(f'   Exécutions: {len(extract_logs.data)}')
print(f'   ✅ Succès: {success_count}/{len(extract_logs.data)}')
print(f'   📊 Villes collectées: {total_collected}')
print(f'   Dernière: {extract_logs.data[0]["execution_time"][:19]}')

# Calcul période
if len(extract_logs.data) > 1:
    first = extract_logs.data[-1]["execution_time"][:13]
    last = extract_logs.data[0]["execution_time"][:13]
    print(f'   📅 Période: {first}h → {last}h')

print('\n' + '='*60)
