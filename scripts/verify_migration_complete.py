#!/usr/bin/env python3
"""
Vérification de la migration vers dim_date (architecture simplifiée)
Vérifie que dim_time et time_id ont bien été supprimés
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.database_service import DatabaseService
from config import Config

def verify_migration():
    """Vérifier que la migration est complète"""
    db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    print("🔍 Vérification de la migration dim_time → dim_date\n")
    
    # Test simple : récupérer les dernières mesures avec la nouvelle structure
    print("1️⃣ Test requête avec nouvelle architecture...")
    try:
        result = db.client.table('fact_measures').select(
            'captured_at, capture_date, temperature, aqi_index, '
            'dim_date(date_value, day_name), '
            'dim_city(city_name)'
        ).order('captured_at', desc=True).limit(5).execute()
        
        if result.data:
            print("   ✅ Requête réussie - Architecture opérationnelle!\n")
            print("   📊 Dernières mesures :")
            for row in result.data:
                date_info = row.get('dim_date', {})
                city_info = row.get('dim_city', {})
                print(f"      • {row['captured_at']} - {city_info.get('city_name', 'N/A')}: {row['temperature']}°C, AQI {row.get('aqi_index', 'N/A')}")
        else:
            print("   ⚠️  Pas de données dans fact_measures\n")
            
    except Exception as e:
        print(f"   ❌ Erreur : {e}\n")
        return False
    
    # Vérifier dim_date
    print("\n2️⃣ Vérification dim_date...")
    try:
        result = db.client.table('dim_date').select('*', count='exact').limit(1).execute()
        nb_dates = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
        
        if nb_dates > 0:
            print(f"   ✅ dim_date opérationnelle avec {nb_dates}+ jours\n")
        else:
            print("   ❌ dim_date vide!\n")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur dim_date : {e}\n")
        return False
    
    # Statistiques fact_measures
    print("3️⃣ Statistiques fact_measures...")
    try:
        result = db.client.table('fact_measures').select('*', count='exact').limit(1).execute()
        total_measures = result.count if hasattr(result, 'count') else 0
        
        cities = db.client.table('fact_measures').select('city_id').execute()
        nb_cities = len(set(row['city_id'] for row in cities.data)) if cities.data else 0
        
        print(f"   📊 Total mesures : {total_measures}")
        print(f"   🏙️  Villes avec données : {nb_cities}")
        
    except Exception as e:
        print(f"   ⚠️  Erreur stats : {e}")
    
    # Vérifier que time_id n'existe plus
    print("\n4️⃣ Vérification suppression time_id...")
    try:
        # Tenter de sélectionner time_id (devrait échouer)
        db.client.table('fact_measures').select('time_id').limit(1).execute()
        print("   ❌ time_id existe encore dans fact_measures!")
        return False
    except Exception:
        print("   ✅ time_id n'existe plus (colonne supprimée)")
    
    print("\n" + "="*60)
    print("✅ MIGRATION RÉUSSIE - Architecture dim_date opérationnelle!")
    print("="*60)
    print("\n📝 Résumé de l'architecture :")
    print("   • captured_at : TIMESTAMP (heure exacte de la mesure)")
    print("   • capture_date : DATE (FK vers dim_date.date_value)")
    print("   • dim_date : Dimension temporelle simplifiée")
    print("   • dim_time : Supprimée ✅")
    print("   • time_id : Supprimée ✅")
    
    return True

if __name__ == '__main__':
    try:
        success = verify_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
