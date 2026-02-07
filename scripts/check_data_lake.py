#!/usr/bin/env python3
"""Script rapide pour vérifier le Data Lake"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Stats
total = client.table('raw_data_lake').select('id', count='exact').execute()
processed = client.table('raw_data_lake').select('id', count='exact').eq('processed', True).execute()
unprocessed = total.count - processed.count

# Dernières entrées
recent = client.table('raw_data_lake').select('*').order('collected_at', desc=True).limit(10).execute()

# Logs
logs = client.table('etl_logs').select('*').order('execution_time', desc=True).limit(5).execute()

print(f'\n📊 DATA LAKE: {total.count} entrées')
print(f'   ✅ Traités: {processed.count}')
print(f'   ⏳ En attente: {unprocessed}')

print('\n📅 Dernières entrées:')
for entry in recent.data:
    status = '✅' if entry['processed'] else '⏳'
    print(f"   {status} {entry['source']:12} {entry['city_name']:12} {entry['collected_at'][:19]}")

print('\n📋 Derniers logs ETL:')
for log in logs.data:
    status = '✅' if log['status'] == 'success' else '❌'
    print(f"   {status} {log['source']:10} {log['records_inserted']} insérés - {log['execution_time'][:19]}")
