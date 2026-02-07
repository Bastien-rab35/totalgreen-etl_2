#!/usr/bin/env python3
"""
Réinitialisation complète et rechargement avec ETL combiné
ATTENTION: Ce script supprime toutes les measures et retraite tout le data lake
"""
import sys
sys.path.insert(0, 'src')
from config import Config
from services.database_service import DatabaseService
from etl_transform_to_db import TransformToDB
import time

db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)

print('='*70)
print('⚠️  RÉINITIALISATION COMPLÈTE + RECHARGEMENT')
print('='*70)

# Vérifier l'état actuel
total_lake = db.client.table('raw_data_lake').select('*', count='exact').execute()
total_measures = db.client.table('measures').select('*', count='exact').execute()

print(f'\n📊 État actuel:')
print(f'   Data Lake: {total_lake.count} entrées')
print(f'   Measures: {total_measures.count} entrées (sera divisé par ~2 après)')

# Confirmation
print('\n⚠️  ATTENTION: Cette opération va:')
print(f'   1. Supprimer les {total_measures.count} measures existantes')
print(f'   2. Marquer les {total_lake.count} entrées du data lake comme non-processed')
print(f'   3. Retraiter TOUT avec le nouveau code combiné (météo+AQI par ligne)')
print(f'   4. Résultat: ~{total_lake.count//2} measures (au lieu de {total_measures.count})')

response = input('\n❓ Continuer? (oui/non): ')
if response.lower() != 'oui':
    print('❌ Opération annulée')
    sys.exit(0)

print('\n🔄 Début de la réinitialisation...')

# Étape 1: Supprimer toutes les measures
print('\n1️⃣  Suppression des measures...')
try:
    result = db.client.table('measures').delete().neq('id', 0).execute()
    print(f'   ✅ Measures supprimées')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
    sys.exit(1)

# Étape 2: Marquer tout le data lake comme non-processed
print('\n2️⃣  Reset du statut du data lake...')
try:
    result = db.client.table('raw_data_lake').update({
        'processed': False,
        'processed_at': None
    }).neq('id', 0).execute()
    print(f'   ✅ {total_lake.count} entrées marquées comme non-processed')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
    sys.exit(1)

# Étape 3: Retraiter TOUT par batch
print('\n3️⃣  Retraitement complet avec ETL combiné...')
print(f'   Estimation: {total_lake.count} entrées → ~{total_lake.count//2} measures combinées')

pipeline = TransformToDB()
batch_size = 1000
total_processed = 0
batch_num = 0

while True:
    batch_num += 1
    print(f'\n   📦 Batch {batch_num} (size={batch_size})...')
    
    stats = pipeline.run(batch_size=batch_size)
    
    if stats['total'] == 0:
        print('   ✅ Traitement terminé (plus de données)')
        break
    
    total_processed += stats['processed_entries']
    print(f'   ✅ {stats["success"]} measures combinées ({stats["processed_entries"]} entrées) - {stats["duration"]}s')
    print(f'   📊 Progression: {total_processed}/{total_lake.count} entrées traitées')
    
    if stats['errors'] > 0:
        print(f'   ⚠️  {stats["errors"]} erreurs dans ce batch')
    
    # Pause pour éviter de surcharger l'API
    if stats['total'] == batch_size:
        time.sleep(0.5)

# Vérification finale
print('\n4️⃣  Vérification finale...')
new_measures = db.client.table('measures').select('*', count='exact').execute()
unprocessed = db.client.table('raw_data_lake').select('*', count='exact').eq('processed', False).execute()
null_temp = db.client.table('measures').select('*', count='exact').is_('temp', 'null').execute()
null_aqi = db.client.table('measures').select('*', count='exact').is_('aqi_index', 'null').execute()

print(f'   ✅ Measures créées: {new_measures.count}')
print(f'   ✅ Data lake non-processed: {unprocessed.count}')
print(f'   📊 Temp NULL: {null_temp.count}/{new_measures.count} ({null_temp.count/new_measures.count*100:.1f}%)')
print(f'   📊 AQI NULL: {null_aqi.count}/{new_measures.count} ({null_aqi.count/new_measures.count*100:.1f}%)')

print('\n' + '='*70)
print('✅ RÉINITIALISATION ET RECHARGEMENT TERMINÉS')
print('='*70)
print(f'\n📈 Résultats:')
print(f'   Avant: {total_measures.count} measures (beaucoup de NULL)')
print(f'   Après: {new_measures.count} measures combinées')
print(f'   Réduction: {total_measures.count - new_measures.count} lignes en moins')
print(f'   Qualité: Temp NULL {null_temp.count/new_measures.count*100:.1f}%, AQI NULL {null_aqi.count/new_measures.count*100:.1f}%')
print('\n' + '='*70)
