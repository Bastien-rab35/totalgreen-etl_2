#!/usr/bin/env python3
"""
Script de déploiement du modèle en étoile sur Supabase
Exécute les scripts SQL pour créer et migrer vers le Data Warehouse
"""
import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.database_service import DatabaseService
from src.config import config

def execute_sql_file(db: DatabaseService, filepath: str, description: str):
    """
    Exécute un fichier SQL via l'API Supabase
    
    Args:
        db: Instance DatabaseService
        filepath: Chemin vers le fichier SQL
        description: Description pour les logs
    """
    print(f"\n{'='*60}")
    print(f"📄 {description}")
    print(f"{'='*60}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Utiliser psycopg2 via le client Supabase
        # Note: Supabase utilise PostgREST, pas de connexion SQL directe
        # On va utiliser la fonction SQL Editor de Supabase
        
        # Découper par blocs DO anonymes et CREATE statements
        import re
        
        # Patterns pour découper intelligemment
        # 1. Blocs DO ... END
        do_blocks = re.findall(r'DO \$\$.*?END \$\$;', sql_content, re.DOTALL)
        
        # 2. Remplacer les blocs DO par des placeholders
        sql_without_do = sql_content
        for i, block in enumerate(do_blocks):
            sql_without_do = sql_without_do.replace(block, f'__DO_BLOCK_{i}__')
        
        # 3. Découper le reste par point-virgules
        statements = [s.strip() for s in sql_without_do.split(';') if s.strip()]
        
        # 4. Remettre les blocs DO
        final_statements = []
        for stmt in statements:
            if '__DO_BLOCK_' in stmt:
                # Remplacer par le vrai bloc
                for i, block in enumerate(do_blocks):
                    stmt = stmt.replace(f'__DO_BLOCK_{i}__', block)
            if stmt and not stmt.startswith('--'):
                final_statements.append(stmt)
        
        print(f"📊 {len(final_statements)} commandes SQL à exécuter...")
        
        # Exécuter via supabase-py (utilise PostgREST)
        # Pour du SQL direct, on doit utiliser la REST API
        import requests
        
        url = f"{config.SUPABASE_URL}/rest/v1/rpc/exec_sql"
        headers = {
            'apikey': config.SUPABASE_KEY,
            'Authorization': f'Bearer {config.SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        success_count = 0
        error_count = 0
        
        for i, stmt in enumerate(final_statements, 1):
            try:
                # Tentative avec RPC exec_sql (si disponible)
                response = requests.post(
                    url,
                    headers=headers,
                    json={'sql': stmt}
                )
                
                if response.status_code in [200, 201, 204]:
                    success_count += 1
                    if i % 10 == 0:
                        print(f"  ✓ {i}/{len(final_statements)} commandes exécutées")
                else:
                    # Erreur mais peut-être que la fonction n'existe pas
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                if 'function exec_sql does not exist' in str(e).lower():
                    print("\n⚠️  La fonction exec_sql n'existe pas sur Supabase")
                    print("📋 Copiez-collez le contenu de ces fichiers dans SQL Editor:")
                    print(f"   1. {filepath}")
                    return False
        
        print(f"\n✅ Résultat: {success_count} succès, {error_count} erreurs")
        
        if error_count > 0:
            print("\n⚠️  Certaines commandes ont échoué")
            print("📋 Solution: Copiez-collez le fichier SQL dans Supabase SQL Editor")
            print(f"   → https://supabase.com/dashboard/project/uqntmecpgswkdchcfwxe/sql")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def verify_tables(db: DatabaseService):
    """Vérifie que les tables du modèle en étoile existent"""
    print(f"\n{'='*60}")
    print("🔍 Vérification des tables créées")
    print(f"{'='*60}")
    
    tables_to_check = [
        'dim_time',
        'dim_city', 
        'dim_weather_condition',
        'dim_air_quality_level',
        'fact_measures'
    ]
    
    for table in tables_to_check:
        try:
            result = db.client.table(table).select('*').limit(1).execute()
            count = len(result.data) if result.data else 0
            print(f"  ✓ {table}: existe")
        except Exception as e:
            print(f"  ✗ {table}: introuvable")
            return False
    
    print("\n✅ Toutes les tables existent!")
    return True

def show_statistics(db: DatabaseService):
    """Affiche les statistiques du modèle en étoile"""
    print(f"\n{'='*60}")
    print("📊 Statistiques du Data Warehouse")
    print(f"{'='*60}")
    
    try:
        # Compter les enregistrements
        tables = {
            'dim_city': 'Villes',
            'dim_time': 'Périodes temporelles',
            'dim_weather_condition': 'Conditions météo',
            'dim_air_quality_level': 'Niveaux AQI',
            'fact_measures': 'Mesures (faits)'
        }
        
        for table, label in tables.items():
            try:
                result = db.client.table(table).select('*', count='exact').execute()
                count = result.count if hasattr(result, 'count') else len(result.data)
                print(f"  {label:30s} : {count:6d} enregistrements")
            except:
                print(f"  {label:30s} : N/A")
        
        print(f"\n✅ Modèle en étoile opérationnel!")
        
    except Exception as e:
        print(f"❌ Erreur lors du calcul des statistiques: {e}")

def main():
    """Point d'entrée principal"""
    print("\n" + "="*60)
    print("🌟 DÉPLOIEMENT DU MODÈLE EN ÉTOILE")
    print("="*60)
    print(f"📅 Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Supabase: {config.SUPABASE_URL}")
    
    # Connexion à Supabase
    print("\n🔌 Connexion à Supabase...")
    db = DatabaseService(config.SUPABASE_URL, config.SUPABASE_KEY)
    print("✅ Connecté")
    
    # Chemins des fichiers SQL
    base_dir = Path(__file__).parent.parent
    star_schema_file = base_dir / 'sql' / 'star_schema.sql'
    migrate_file = base_dir / 'sql' / 'migrate_to_star_schema.sql'
    
    # Vérifier que les fichiers existent
    if not star_schema_file.exists():
        print(f"❌ Fichier introuvable: {star_schema_file}")
        return 1
    
    if not migrate_file.exists():
        print(f"❌ Fichier introuvable: {migrate_file}")
        return 1
    
    print("\n⚠️  MÉTHODE D'EXÉCUTION RECOMMANDÉE")
    print("="*60)
    print("L'API Supabase (PostgREST) ne permet pas d'exécuter du SQL arbitraire.")
    print("Vous devez copier-coller les fichiers SQL dans le SQL Editor de Supabase.")
    print()
    print("📋 ÉTAPES:")
    print("1. Ouvrir: https://supabase.com/dashboard/project/uqntmecpgswkdchcfwxe/sql")
    print("2. Créer une nouvelle query")
    print(f"3. Copier-coller le contenu de: {star_schema_file}")
    print("4. Exécuter (Run)")
    print(f"5. Copier-coller le contenu de: {migrate_file}")
    print("6. Exécuter (Run)")
    print()
    print("="*60)
    
    # Afficher le contenu pour faciliter le copier-coller
    print("\n📄 CONTENU À COPIER - STAR SCHEMA")
    print("="*60)
    print(f"\nFichier: {star_schema_file}")
    print("-" * 60)
    
    # Option: demander à l'utilisateur de confirmer
    response = input("\nVoulez-vous afficher le SQL ici pour copier-coller? (o/n): ")
    
    if response.lower() == 'o':
        with open(star_schema_file, 'r') as f:
            print(f.read())
        
        print("\n" + "="*60)
        input("Appuyez sur Entrée après avoir exécuté ce SQL dans Supabase...")
        
        print("\n📄 CONTENU À COPIER - MIGRATION")
        print("="*60)
        print(f"\nFichier: {migrate_file}")
        print("-" * 60)
        
        with open(migrate_file, 'r') as f:
            print(f.read())
        
        print("\n" + "="*60)
        input("Appuyez sur Entrée après avoir exécuté ce SQL dans Supabase...")
        
        # Vérifier les tables
        if verify_tables(db):
            show_statistics(db)
            return 0
        else:
            print("\n⚠️  Les tables ne semblent pas créées. Vérifiez les erreurs dans SQL Editor.")
            return 1
    else:
        print("\n✅ Instructions affichées ci-dessus.")
        print("📖 Référez-vous aux fichiers SQL dans le dossier sql/")
        return 0

if __name__ == '__main__':
    sys.exit(main())
