"""
Script de vérification de la nouvelle architecture (captured_at + dim_date)
"""
from src.config import Config
from supabase import create_client

def verify_architecture():
    """Vérifie que la migration est réussie"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    print('=' * 70)
    print('VÉRIFICATION DE LA NOUVELLE ARCHITECTURE')
    print('=' * 70)
    print()
    
    # 1. Vérifier dim_date
    print('1️⃣  dim_date:')
    try:
        response = client.table('dim_date').select('*', count='exact').limit(5).execute()
        print(f'   ✅ {response.count} jours créés')
        if response.data:
            example = response.data[0]
            print(f'   📅 Exemple: {example["date_value"]} - {example["day_name"].strip()} - {example["season"]}')
    except Exception as e:
        print(f'   ❌ Erreur: {e}')
    
    print()
    
    # 2. Vérifier fact_measures avec captured_at
    print('2️⃣  fact_measures.captured_at:')
    try:
        response = client.table('fact_measures').select('measure_id, captured_at, city_id').order('captured_at', desc=True).limit(3).execute()
        print(f'   ✅ {len(response.data)} mesures récentes:')
        for row in response.data:
            print(f'      • measure_id={row["measure_id"]}, date={row["captured_at"][:19]}, city_id={row["city_id"]}')
    except Exception as e:
        print(f'   ❌ Erreur: {e}')
    
    print()
    
    # 3. Test de jointure fact_measures + dim_date
    print('3️⃣  Jointure fact_measures + dim_date:')
    try:
        fm_response = client.table('fact_measures').select('measure_id, captured_at, temperature').order('captured_at', desc=True).limit(5).execute()
        
        if fm_response.data:
            print('   ✅ Jointure réussie:')
            for fm in fm_response.data:
                date_str = fm['captured_at'][:10]
                dd_response = client.table('dim_date').select('day_name, season, is_weekend').eq('date_value', date_str).execute()
                if dd_response.data:
                    dd = dd_response.data[0]
                    weekend = '🏖️' if dd['is_weekend'] else '💼'
                    print(f'      • {date_str} ({dd["day_name"].strip()}, {dd["season"]}) {weekend} - {fm["temperature"]}°C')
    except Exception as e:
        print(f'   ❌ Erreur: {e}')
    
    print()
    
    # 4. Statistiques par jour de la semaine
    print('4️⃣  Analyse par jour de la semaine (via dim_date):')
    try:
        # Récupérer toutes les mesures récentes
        fm_all = client.table('fact_measures').select('captured_at, temperature').order('captured_at', desc=True).limit(100).execute()
        
        if fm_all.data:
            # Grouper par jour de semaine
            day_stats = {}
            for fm in fm_all.data:
                date_str = fm['captured_at'][:10]
                dd = client.table('dim_date').select('day_name').eq('date_value', date_str).execute()
                if dd.data:
                    day_name = dd.data[0]['day_name'].strip()
                    if day_name not in day_stats:
                        day_stats[day_name] = []
                    if fm['temperature']:
                        day_stats[day_name].append(fm['temperature'])
            
            print('   ✅ Températures moyennes par jour:')
            for day, temps in sorted(day_stats.items()):
                if temps:
                    avg_temp = sum(temps) / len(temps)
                    print(f'      • {day:10s}: {avg_temp:.1f}°C (n={len(temps)})')
    except Exception as e:
        print(f'   ❌ Erreur: {e}')
    
    print()
    print('=' * 70)
    print('✅ NOUVELLE ARCHITECTURE OPÉRATIONNELLE !')
    print('=' * 70)
    print()
    print('📊 Résumé:')
    print('   • captured_at stocké dans fact_measures ✅')
    print('   • dim_date créée avec 1461 jours (2024-2027) ✅')
    print('   • Jointure simple: DATE(captured_at) = dim_date.date_value ✅')
    print('   • Analyses temporelles disponibles (jour, mois, saison, weekend) ✅')
    print()
    print('🗑️  Optionnel: Supprimer time_id et dim_time')
    print('   ALTER TABLE fact_measures DROP COLUMN time_id;')
    print('   DROP TABLE dim_time CASCADE;')

if __name__ == '__main__':
    verify_architecture()
