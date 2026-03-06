#!/usr/bin/env python3
"""
Script de test pour vérifier la table anomalies
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.services.database_service import DatabaseService

def main():
    try:
        print("Connexion à Supabase...")
        db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        print("\n1. Test de connexion à la table 'anomalies'...")
        
        try:
            # Tenter de lire la table
            response = db.client.table('anomalies').select('*').limit(1).execute()
            print(f"✓ Table 'anomalies' existe et accessible")
            print(f"  Nombre de lignes testées: {len(response.data)}")
            
            # Compter le nombre total d'anomalies
            count_response = db.client.table('anomalies').select('*', count='exact').execute()
            print(f"  Total anomalies en BDD: {count_response.count}")
            
        except Exception as e:
            print(f"✗ Erreur d'accès à la table 'anomalies': {e}")
            print("\n⚠ La table 'anomalies' n'existe probablement pas encore.")
            print("   Exécutez le script SQL: sql/anomalies_table.sql dans Supabase SQL Editor")
            return False
        
        print("\n2. Test d'insertion d'une anomalie de test...")
        
        try:
            import uuid
            from datetime import datetime, timezone
            
            test_anomaly = {
                'validation_run_id': str(uuid.uuid4()),
                'severity': 'info',
                'category': 'test',
                'message': 'Test de connexion - anomalie fictive',
                'detected_at': datetime.now(timezone.utc).isoformat(),
                'validation_period_hours': 24,
                'details': '{"test": true}'
            }
            
            insert_response = db.client.table('anomalies').insert(test_anomaly).execute()
            print(f"✓ Insertion réussie")
            print(f"  ID créé: {insert_response.data[0]['id']}")
            
            # Supprimer l'anomalie de test
            db.client.table('anomalies').delete().eq('category', 'test').execute()
            print(f"✓ Anomalie de test supprimée")
            
        except Exception as e:
            print(f"✗ Erreur d'insertion: {e}")
            return False
        
        print("\n✓ Tous les tests ont réussi - la table est opérationnelle")
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
