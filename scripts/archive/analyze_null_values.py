"""
Script d'analyse des valeurs NULL dans fact_measures
"""
from src.config import Config
from supabase import create_client

def analyze_null_values():
    """Analyse les valeurs NULL dans fact_measures"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    print('=' * 60)
    print('ANALYSE DES VALEURS NULL DANS fact_measures')
    print('=' * 60)
    print()
    
    # Compter les NULL par colonne
    response = client.table('fact_measures').select('*').execute()
    data = response.data
    
    if not data:
        print("❌ Aucune donnée dans fact_measures")
        return
    
    total = len(data)
    print(f"📊 Total mesures: {total}\n")
    
    # Colonnes à analyser
    fields = [
        'temperature', 'humidity', 'pressure', 'wind_speed',
        'aqi_index', 'pm25', 'pm10', 'no2', 'o3', 'so2', 'co',
        'weather_condition_id', 'aqi_level_id'
    ]
    
    print(f"{'Colonne':<25} {'NULL':<8} {'%':<8} {'Valides':<8}")
    print('-' * 60)
    
    null_summary = {}
    
    for field in fields:
        null_count = sum(1 for row in data if row.get(field) is None)
        valid_count = total - null_count
        pct = (null_count / total * 100) if total > 0 else 0
        
        null_summary[field] = {
            'null_count': null_count,
            'valid_count': valid_count,
            'percentage': pct
        }
        
        icon = '❌' if null_count > 0 else '✅'
        print(f"{icon} {field:<23} {null_count:<8} {pct:>6.1f}% {valid_count:<8}")
    
    # Résumé par catégorie
    print('\n' + '=' * 60)
    print('RÉSUMÉ PAR CATÉGORIE')
    print('=' * 60)
    
    weather_fields = ['temperature', 'humidity', 'pressure', 'wind_speed']
    aqi_fields = ['aqi_index', 'pm25', 'pm10', 'no2', 'o3', 'so2', 'co']
    fk_fields = ['weather_condition_id', 'aqi_level_id']
    
    for category, fields_list in [
        ('Météo', weather_fields),
        ('Qualité air', aqi_fields),
        ('Clés étrangères', fk_fields)
    ]:
        total_null = sum(null_summary[f]['null_count'] for f in fields_list if f in null_summary)
        avg_pct = sum(null_summary[f]['percentage'] for f in fields_list if f in null_summary) / len(fields_list)
        print(f"\n{category}:")
        print(f"  Total NULL: {total_null}")
        print(f"  Moyenne: {avg_pct:.1f}%")
    
    # Détection des patterns
    print('\n' + '=' * 60)
    print('PATTERNS DÉTECTÉS')
    print('=' * 60)
    
    # Mesures avec NULL dans AQI
    aqi_null_rows = [row for row in data if row.get('aqi_index') is None]
    if aqi_null_rows:
        print(f"\n⚠️  {len(aqi_null_rows)} mesures sans aqi_index")
        cities_aqi_null = {}
        for row in aqi_null_rows:
            city_id = row.get('city_id')
            cities_aqi_null[city_id] = cities_aqi_null.get(city_id, 0) + 1
        print(f"   Villes impactées: {len(cities_aqi_null)}")
    
    # Mesures avec NULL dans température
    temp_null_rows = [row for row in data if row.get('temperature') is None]
    if temp_null_rows:
        print(f"\n⚠️  {len(temp_null_rows)} mesures sans température")
    
    # Mesures complètes
    complete_rows = [
        row for row in data 
        if all(row.get(f) is not None for f in ['temperature', 'humidity', 'pressure', 'aqi_index'])
    ]
    complete_pct = (len(complete_rows) / total * 100) if total > 0 else 0
    print(f"\n✅ {len(complete_rows)} mesures complètes ({complete_pct:.1f}%)")

if __name__ == '__main__':
    analyze_null_values()
