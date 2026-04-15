#!/usr/bin/env python3
"""
Script de nettoyage des problèmes de qualité des données.

Corrige automatiquement :
- Les doublons (même city_id + captured_at)
- Les mesures avec captured_at dans le futur
- Optionnellement : autres problèmes de cohérence

Usage:
    python scripts/cleanup_data_quality_issues.py [--dry-run]
    
Options:
    --dry-run    Mode simulation (pas de modifications réelles)
"""

import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Ajouter le répertoire parent au path
sys.path.insert(0, '.')

from src.services.database_service import DatabaseService
from src.config import Config


class DataQualityCleanup:
    """Nettoyage automatique des problèmes de qualité des données."""
    
    def __init__(self, dry_run: bool = False):
        self.db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self.dry_run = dry_run
        self.issues_fixed = {
            'duplicates': 0,
            'future_dates': 0,
            'total_deleted': 0
        }
    
    def find_duplicates(self) -> List[Dict]:
        """Trouve les doublons (même city_id + captured_at)."""
        print("\n🔍 Recherche des doublons...")
        
        # Récupérer toutes les mesures
        response = self.db.client.table('fact_measures').select(
            'measure_id, city_id, captured_at, created_at'
        ).order('city_id', desc=False).order('captured_at', desc=False).execute()
        
        measures = response.data
        
        # Grouper par (city_id, captured_at)
        groups = {}
        for measure in measures:
            key = (measure['city_id'], measure['captured_at'])
            if key not in groups:
                groups[key] = []
            groups[key].append(measure)
        
        # Identifier les doublons
        duplicates = []
        for key, group in groups.items():
            if len(group) > 1:
                # Trier par created_at DESC pour garder le plus récent
                group.sort(key=lambda x: x['created_at'], reverse=True)
                # Les doublons sont tous sauf le premier
                duplicates.extend(group[1:])
        
        return duplicates
    
    def find_future_dates(self) -> List[Dict]:
        """Trouve les mesures avec captured_at dans le futur."""
        print("\n🔍 Recherche des dates futures...")
        
        now = datetime.now(timezone.utc).isoformat()
        
        response = self.db.client.table('fact_measures').select(
            'measure_id, city_id, captured_at, created_at'
        ).gt('captured_at', now).execute()
        
        return response.data
    
    def delete_measures(self, measure_ids: List[int], reason: str) -> int:
        """Supprime les mesures par leurs IDs."""
        if not measure_ids:
            return 0
        
        if self.dry_run:
            print(f"   [DRY-RUN] Suppression de {len(measure_ids)} mesures ({reason})")
            return len(measure_ids)
        
        deleted_count = 0
        batch_size = 50  # Supprimer par lots
        
        for i in range(0, len(measure_ids), batch_size):
            batch = measure_ids[i:i + batch_size]
            try:
                self.db.client.table('fact_measures').delete().in_(
                    'measure_id', batch
                ).execute()
                deleted_count += len(batch)
                print(f"   Supprimé {deleted_count}/{len(measure_ids)} mesures...")
            except Exception as e:
                print(f"   ❌ Erreur lors de la suppression: {e}")
        
        return deleted_count
    
    def cleanup_duplicates(self) -> int:
        """Nettoie les doublons en gardant le plus récent."""
        duplicates = self.find_duplicates()
        
        if not duplicates:
            print("   ✅ Aucun doublon trouvé")
            return 0
        
        print(f"   ⚠️  {len(duplicates)} doublons trouvés")
        
        # Afficher quelques exemples
        print("\n   Exemples de doublons:")
        for dup in duplicates[:5]:
            print(f"      - measure_id={dup['measure_id']}, "
                  f"city_id={dup['city_id']}, "
                  f"captured_at={dup['captured_at']}")
        
        if len(duplicates) > 5:
            print(f"      ... et {len(duplicates) - 5} autres")
        
        # Supprimer les doublons
        measure_ids = [d['measure_id'] for d in duplicates]
        deleted = self.delete_measures(measure_ids, "doublons")
        
        self.issues_fixed['duplicates'] = deleted
        return deleted
    
    def cleanup_future_dates(self) -> int:
        """Supprime les mesures avec dates futures."""
        future_measures = self.find_future_dates()
        
        if not future_measures:
            print("   ✅ Aucune date future trouvée")
            return 0
        
        print(f"   ⚠️  {len(future_measures)} mesures avec dates futures")
        
        # Afficher les mesures futures
        print("\n   Mesures futures:")
        for measure in future_measures:
            print(f"      - measure_id={measure['measure_id']}, "
                  f"captured_at={measure['captured_at']}")
        
        # Supprimer les mesures futures
        measure_ids = [m['measure_id'] for m in future_measures]
        deleted = self.delete_measures(measure_ids, "dates futures")
        
        self.issues_fixed['future_dates'] = deleted
        return deleted
    
    def run(self):
        """Exécute le nettoyage complet."""
        print("=" * 70)
        print("NETTOYAGE QUALITÉ DES DONNÉES")
        print("=" * 70)
        
        if self.dry_run:
            print("\n⚠️  MODE DRY-RUN - Aucune modification réelle")
        
        print(f"\nDate: {datetime.now(timezone.utc).isoformat()}")
        
        # 1. Nettoyer les doublons
        print("\n" + "=" * 70)
        print("1. NETTOYAGE DES DOUBLONS")
        print("=" * 70)
        duplicates_deleted = self.cleanup_duplicates()
        
        # 2. Nettoyer les dates futures
        print("\n" + "=" * 70)
        print("2. NETTOYAGE DES DATES FUTURES")
        print("=" * 70)
        futures_deleted = self.cleanup_future_dates()
        
        # Résumé
        self.issues_fixed['total_deleted'] = duplicates_deleted + futures_deleted
        
        print("\n" + "=" * 70)
        print("RÉSUMÉ DU NETTOYAGE")
        print("=" * 70)
        print(f"\nProblèmes corrigés:")
        print(f"   - Doublons supprimés: {self.issues_fixed['duplicates']}")
        print(f"   - Dates futures supprimées: {self.issues_fixed['future_dates']}")
        print(f"\nTotal mesures supprimées: {self.issues_fixed['total_deleted']}")
        
        if self.dry_run:
            print("\n⚠️  MODE DRY-RUN - Relancer sans --dry-run pour appliquer les modifications")
        else:
            print("\n✅ Nettoyage terminé avec succès")
        
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Nettoie automatiquement les problèmes de qualité des données"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Mode simulation (pas de modifications réelles)"
    )
    
    args = parser.parse_args()
    
    # Exécuter le nettoyage
    cleanup = DataQualityCleanup(dry_run=args.dry_run)
    cleanup.run()
    
    # Exit code basé sur les problèmes trouvés
    if cleanup.issues_fixed['total_deleted'] > 0:
        sys.exit(0)  # Succès avec corrections
    else:
        sys.exit(0)  # Succès sans corrections nécessaires


if __name__ == '__main__':
    main()
