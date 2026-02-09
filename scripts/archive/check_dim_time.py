"""
Script de vérification de la dimension temps
"""
from src.config import Config
from supabase import create_client

def check_dim_time():
    """Vérifie la dimension temps"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    print('=' * 70)
    print('ANALYSE DE dim_time')
    print('=' * 70)
    print()
    
    # Premiers enregistrements
    response = client.table('dim_time').select('*').order('time_id').limit(5).execute()
    if response.data:
        print('📊 Premiers enregistrements:')
        for row in response.data:
            print(f"  time_id={row.get('time_id')}, date={row.get('date_only')}, "
                  f"hour={row.get('hour_24')}h, {row.get('day_name')}")
    
    # Plage de dates
    print('\n📅 Plage de dates:')
    min_response = client.table('dim_time').select('date_only').order('date_only', desc=False).limit(1).execute()
    max_response = client.table('dim_time').select('date_only').order('date_only', desc=True).limit(1).execute()
    
    if min_response.data and max_response.data:
        min_date = min_response.data[0]['date_only']
        max_date = max_response.data[0]['date_only']
        print(f'  Min: {min_date}')
        print(f'  Max: {max_date}')
    
    # Total
    count_response = client.table('dim_time').select('time_id', count='exact').execute()
    print(f'\n📈 Total: {count_response.count} enregistrements')
    
    # Analyser fact_measures
    print('\n' + '=' * 70)
    print('ANALYSE DE fact_measures')
    print('=' * 70)
    print()
    
    fm_response = client.table('fact_measures').select('measure_id, time_id').order('measure_id').limit(5).execute()
    
    if fm_response.data:
        print('📊 Premiers enregistrements:')
        for row in fm_response.data:
            time_id = row.get('time_id')
            measure_id = row.get('measure_id')
            
            # Chercher dans dim_time
            time_data = client.table('dim_time').select('date_only, hour').eq('time_id', time_id).execute()
            
            if time_data.data:
                date = time_data.data[0]['date_only']
                hour = time_data.data[0]['hour']
                print(f"  measure_id={measure_id}, time_id={time_id}, date={date}, hour={hour}h")
            else:
                print(f"  measure_id={measure_id}, time_id={time_id} ❌ NON TROUVÉ dans dim_time")
    
    # Dates récentes dans fact_measures
    print('\n📅 Dates les plus récentes dans fact_measures:')
    fm_recent = client.table('fact_measures').select('measure_id, time_id').order('measure_id', desc=True).limit(5).execute()
    
    if fm_recent.data:
        for row in fm_recent.data:
            time_id = row.get('time_id')
            time_data = client.table('dim_time').select('date_only, hour').eq('time_id', time_id).execute()
            
            if time_data.data:
                date = time_data.data[0]['date_only']
                hour = time_data.data[0]['hour']
                print(f"  measure_id={row.get('measure_id')}, date={date}, hour={hour}h")
    
    # Diagnostic
    print('\n' + '=' * 70)
    print('DIAGNOSTIC')
    print('=' * 70)
    print()
    
    if min_response.data and max_response.data:
        min_date = min_response.data[0]['date_only']
        max_date = max_response.data[0]['date_only']
        
        if '2024-01' in min_date and '2024-01' in max_date:
            print('⚠️  PROBLÈME DÉTECTÉ:')
            print('   dim_time contient uniquement des dates de janvier 2024')
            print('   Les données de 2026 ne peuvent pas être insérées correctement')
            print()
            print('📋 SOLUTIONS:')
            print('   1. Régénérer dim_time avec des dates 2024-2027')
            print('   2. Ou mieux: stocker captured_at dans fact_measures')
            print('      et utiliser dim_date pour attributs dérivés uniquement')

if __name__ == '__main__':
    check_dim_time()
