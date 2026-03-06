#!/usr/bin/env python3
"""
Script de validation de la qualité des données

Vérifie l'intégrité et la qualité des données importées dans fact_measures.
Conçu pour être exécuté par GitHub Actions après chaque import de données.

VÉRIFICATIONS:
1. Intégrité structurelle (clés étrangères, NULL, doublons)
2. Cohérence temporelle (gaps, ordre chronologique)
3. Limites physiques (business rules)
4. Anomalies statistiques (outliers)
5. Couverture des données (toutes les villes, période complète)

UTILISATION:
    # Valider les données des dernières 24h
    python scripts/validate_data_quality.py
    
    # Valider une période spécifique
    python scripts/validate_data_quality.py --hours 48
    
    # Mode strict (échoue si anomalies)
    python scripts/validate_data_quality.py --strict

EXIT CODES:
    0: Aucun problème critique
    1: Problèmes critiques détectés
    2: Erreur d'exécution
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import argparse
import uuid
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.services.database_service import DatabaseService


class DataQualityValidator:
    """Validateur de qualité des données"""
    
    # Limites physiques (business rules)
    LIMITS = {
        'temperature': (-50, 60),
        'pressure': (870, 1084),
        'humidity': (0, 100),
        'wind_speed': (0, 200),
        'clouds': (0, 100),
        'visibility': (0, 50000),
        'uvi': (0, 15),
        'aqi': (0, 500),
        'pm25': (0, 1000),
        'pm10': (0, 2000),
        'no2': (0, 500),
        'o3': (0, 800),
        'so2': (0, 500),
        'co': (0, 50000)
    }
    
    # Villes attendues (city_id)
    EXPECTED_CITIES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    CITY_NAMES = {
        1: 'Paris', 2: 'Marseille', 3: 'Lyon', 4: 'Toulouse',
        5: 'Nice', 6: 'Nantes', 7: 'Montpellier', 8: 'Strasbourg',
        9: 'Bordeaux', 10: 'Lille'
    }
    
    def __init__(self, db: DatabaseService, hours: int = 24):
        """
        Initialise le validateur
        
        Args:
            db: Instance DatabaseService
            hours: Nombre d'heures à analyser (depuis maintenant)
        """
        self.db = db
        self.hours = hours
        self.start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        self.validation_run_id = str(uuid.uuid4())  # ID unique pour ce run
        self.issues = {
            'critical': [],
            'warning': [],
            'info': []
        }
        
    def log_issue(self, severity: str, category: str, message: str, details: Dict = None):
        """
        Enregistre un problème détecté
        
        Args:
            severity: 'critical', 'warning', ou 'info'
            category: Catégorie du problème
            message: Description du problème
            details: Détails supplémentaires
        """
        issue = {
            'category': category,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details or {}
        }
        self.issues[severity].append(issue)
        
    def validate_structural_integrity(self, measures: List[Dict]) -> None:
        """Vérifie l'intégrité structurelle des données"""
        
        print("\n1. Vérification intégrité structurelle...")
        
        if not measures:
            self.log_issue('critical', 'data_missing', 
                          f"Aucune donnée trouvée dans les {self.hours} dernières heures")
            return
        
        # Vérifier les clés étrangères NULL
        null_checks = {
            'city_id': 0,
            'capture_date': 0,
            'captured_at': 0
        }
        
        for measure in measures:
            for field in null_checks:
                if measure.get(field) is None:
                    null_checks[field] += 1
        
        for field, count in null_checks.items():
            if count > 0:
                self.log_issue('critical', 'null_values',
                              f"{count} mesures avec {field} NULL sur {len(measures)}")
        
        # Vérifier les doublons (même city + timestamp)
        seen = set()
        duplicates = 0
        
        for measure in measures:
            key = (measure.get('city_id'), measure.get('captured_at'))
            if key in seen:
                duplicates += 1
            seen.add(key)
        
        if duplicates > 0:
            self.log_issue('critical', 'duplicates',
                          f"{duplicates} doublons détectés (même city_id + captured_at)")
        
        print(f"   Total mesures: {len(measures)}")
        print(f"   Doublons: {duplicates}")
        print(f"   Valeurs NULL: {sum(null_checks.values())}")
        
    def validate_temporal_coherence(self, measures: List[Dict]) -> None:
        """Vérifie la cohérence temporelle"""
        
        print("\n2. Vérification cohérence temporelle...")
        
        # Vérifier created_at vs captured_at
        incoherent_dates = 0
        future_dates = 0
        now = datetime.now(timezone.utc)
        
        for measure in measures:
            created = measure.get('created_at')
            captured = measure.get('captured_at')
            
            if created and captured:
                # Convertir en datetime si string
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if isinstance(captured, str):
                    captured = datetime.fromisoformat(captured.replace('Z', '+00:00'))
                
                # Assurer timezone-aware
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if captured.tzinfo is None:
                    captured = captured.replace(tzinfo=timezone.utc)
                
                # created_at devrait être >= captured_at
                if created < captured:
                    incoherent_dates += 1
                
                # Vérifier dates futures
                if captured > now:
                    future_dates += 1
        
        if incoherent_dates > 0:
            self.log_issue('warning', 'temporal_coherence',
                          f"{incoherent_dates} mesures avec created_at < captured_at")
        
        if future_dates > 0:
            self.log_issue('critical', 'temporal_coherence',
                          f"{future_dates} mesures avec captured_at dans le futur")
        
        # Vérifier gaps temporels par ville
        gaps = self.check_temporal_gaps(measures)
        if gaps:
            total_gaps = sum(len(g) for g in gaps.values())
            self.log_issue('warning', 'temporal_gaps',
                          f"{total_gaps} gaps temporels détectés dans {len(gaps)} villes",
                          details={'gaps': gaps})
        
        print(f"   Incohérences temporelles: {incoherent_dates}")
        print(f"   Dates futures: {future_dates}")
        print(f"   Gaps temporels: {total_gaps if gaps else 0}")
        
    def check_temporal_gaps(self, measures: List[Dict]) -> Dict[int, List[Tuple]]:
        """
        Détecte les gaps temporels (>2h sans données) par ville
        
        Returns:
            Dict {city_id: [(start, end, duration_hours)]}
        """
        from collections import defaultdict
        
        # Grouper par ville et trier par timestamp
        by_city = defaultdict(list)
        
        for measure in measures:
            city_id = measure.get('city_id')
            captured = measure.get('captured_at')
            
            if city_id and captured:
                if isinstance(captured, str):
                    captured = datetime.fromisoformat(captured.replace('Z', '+00:00'))
                # Assurer timezone-aware
                if captured.tzinfo is None:
                    captured = captured.replace(tzinfo=timezone.utc)
                by_city[city_id].append(captured)
        
        # Détecter les gaps (>2h sans données)
        gaps = {}
        
        for city_id, timestamps in by_city.items():
            timestamps.sort()
            city_gaps = []
            
            for i in range(len(timestamps) - 1):
                diff = timestamps[i + 1] - timestamps[i]
                if diff > timedelta(hours=2):
                    city_gaps.append((
                        timestamps[i].isoformat(),
                        timestamps[i + 1].isoformat(),
                        diff.total_seconds() / 3600
                    ))
            
            if city_gaps:
                gaps[city_id] = city_gaps
        
        return gaps
    
    def save_anomalies_to_db(self) -> None:
        """
        Sauvegarde toutes les anomalies détectées dans la table anomalies
        """
        try:
            anomalies_to_insert = []
            
            for severity in ['critical', 'warning', 'info']:
                for issue in self.issues[severity]:
                    anomaly = {
                        'validation_run_id': self.validation_run_id,
                        'severity': severity,
                        'category': issue['category'],
                        'message': issue['message'],
                        'detected_at': issue['timestamp'],
                        'validation_period_hours': self.hours,
                        'details': json.dumps(issue['details']) if issue['details'] else None
                    }
                    anomalies_to_insert.append(anomaly)
            
            if anomalies_to_insert:
                # Insérer toutes les anomalies en une seule requête
                self.db.client.table('anomalies').insert(anomalies_to_insert).execute()
                print(f"\n✓ {len(anomalies_to_insert)} anomalie(s) sauvegardée(s) en BDD (run_id: {self.validation_run_id[:8]}...)")
            else:
                print(f"\n✓ Aucune anomalie détectée - rien à sauvegarder (run_id: {self.validation_run_id[:8]}...)")
                
        except Exception as e:
            print(f"\n⚠ Erreur lors de la sauvegarde des anomalies en BDD: {e}")
            # On ne bloque pas la validation si la sauvegarde échoue
        
    def validate_business_rules(self, measures: List[Dict]) -> None:
        """Vérifie les limites physiques (business rules)"""
        
        print("\n3. Vérification limites physiques...")
        
        violations = {}
        
        for measure in measures:
            for field, (min_val, max_val) in self.LIMITS.items():
                value = measure.get(field)
                
                if value is not None:
                    if value < min_val or value > max_val:
                        key = f"{field}_out_of_bounds"
                        if key not in violations:
                            violations[key] = {'count': 0, 'examples': []}
                        
                        violations[key]['count'] += 1
                        
                        if len(violations[key]['examples']) < 3:
                            violations[key]['examples'].append({
                                'city_id': measure.get('city_id'),
                                'captured_at': measure.get('captured_at'),
                                'value': value,
                                'limits': f"[{min_val}, {max_val}]"
                            })
        
        if violations:
            total = sum(v['count'] for v in violations.values())
            self.log_issue('critical', 'business_rules',
                          f"{total} violations de limites physiques",
                          details={'violations': violations})
        
        print(f"   Violations: {len(violations)} types différents")
        for key, data in violations.items():
            print(f"      - {key}: {data['count']} occurrences")
        
    def validate_data_coverage(self, measures: List[Dict]) -> None:
        """Vérifie la couverture des données (toutes les villes)"""
        
        print("\n4. Vérification couverture des données...")
        
        # Compter les mesures par ville
        city_counts = {}
        for measure in measures:
            city_id = measure.get('city_id')
            if city_id:
                city_counts[city_id] = city_counts.get(city_id, 0) + 1
        
        # Villes manquantes
        missing_cities = set(self.EXPECTED_CITIES) - set(city_counts.keys())
        
        if missing_cities:
            missing_names = [self.CITY_NAMES.get(c, f"ID {c}") for c in missing_cities]
            self.log_issue('warning', 'data_coverage',
                          f"{len(missing_cities)} villes sans données : {', '.join(missing_names)}")
        
        # Villes avec peu de données (< 50% de la moyenne)
        if city_counts:
            avg_count = sum(city_counts.values()) / len(city_counts)
            low_coverage = {
                city_id: count for city_id, count in city_counts.items()
                if count < avg_count * 0.5
            }
            
            if low_coverage:
                details = {
                    self.CITY_NAMES.get(c, f"ID {c}"): count
                    for c, count in low_coverage.items()
                }
                self.log_issue('info', 'data_coverage',
                              f"{len(low_coverage)} villes avec couverture faible",
                              details={'cities': details, 'average': avg_count})
        
        print(f"   Villes avec données: {len(city_counts)}/{len(self.EXPECTED_CITIES)}")
        print(f"   Villes manquantes: {len(missing_cities)}")
        
        for city_id in sorted(city_counts.keys()):
            city_name = self.CITY_NAMES.get(city_id, f"ID {city_id}")
            print(f"      - {city_name}: {city_counts[city_id]} mesures")
        
    def validate_statistical_outliers(self, measures: List[Dict]) -> None:
        """Détecte les valeurs aberrantes statistiques (outliers)"""
        
        print("\n5. Détection outliers statistiques...")
        
        import numpy as np
        
        # Champs numériques à analyser
        numeric_fields = ['temperature', 'humidity', 'pressure', 'aqi', 'pm25', 'pm10']
        
        outliers = {}
        
        for field in numeric_fields:
            values = [m.get(field) for m in measures if m.get(field) is not None]
            
            if len(values) < 10:  # Pas assez de données
                continue
            
            values = np.array(values)
            mean = np.mean(values)
            std = np.std(values)
            
            # Détecter outliers (> 3 sigma)
            z_scores = np.abs((values - mean) / std) if std > 0 else np.zeros_like(values)
            outlier_indices = np.where(z_scores > 3)[0]
            
            if len(outlier_indices) > 0:
                outliers[field] = {
                    'count': len(outlier_indices),
                    'percentage': len(outlier_indices) / len(values) * 100,
                    'mean': float(mean),
                    'std': float(std),
                    'max_z_score': float(np.max(z_scores))
                }
        
        if outliers:
            total = sum(o['count'] for o in outliers.values())
            self.log_issue('info', 'statistical_outliers',
                          f"{total} outliers statistiques détectés (>3σ)",
                          details={'outliers': outliers})
        
        print(f"   Outliers détectés: {len(outliers)} champs")
        for field, data in outliers.items():
            print(f"      - {field}: {data['count']} ({data['percentage']:.1f}%) - max Z={data['max_z_score']:.1f}")
        
    def run_validation(self) -> bool:
        """
        Exécute toutes les validations
        
        Returns:
            True si validation OK, False si problèmes critiques
        """
        print("\n" + "="*70)
        print("VALIDATION QUALITÉ DES DONNÉES")
        print("="*70)
        print(f"\nPériode analysée: {self.hours}h (depuis {self.start_time.isoformat()})")
        
        # Charger les données
        print("\nChargement des données...")
        
        try:
            response = self.db.client.table('fact_measures') \
                .select('*') \
                .gte('captured_at', self.start_time.isoformat()) \
                .execute()
            
            measures = response.data
            
        except Exception as e:
            print(f"\nERREUR: Impossible de charger les données: {e}")
            return False
        
        # Exécuter les validations
        self.validate_structural_integrity(measures)
        self.validate_temporal_coherence(measures)
        self.validate_business_rules(measures)
        self.validate_data_coverage(measures)
        self.validate_statistical_outliers(measures)
        
        # Rapport final
        self.print_report()
        
        # Sauvegarder les anomalies en BDD
        self.save_anomalies_to_db()
        
        # Retourner True si pas de problèmes critiques
        return len(self.issues['critical']) == 0
        
    def print_report(self) -> None:
        """Affiche le rapport de validation"""
        
        print("\n" + "="*70)
        print("RAPPORT DE VALIDATION")
        print("="*70)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        print(f"\nTotal problèmes: {total_issues}")
        print(f"   CRITICAL: {len(self.issues['critical'])}")
        print(f"   WARNING:  {len(self.issues['warning'])}")
        print(f"   INFO:     {len(self.issues['info'])}")
        
        # Détails par sévérité
        for severity in ['critical', 'warning', 'info']:
            issues = self.issues[severity]
            
            if not issues:
                continue
            
            print(f"\n{severity.upper()}:")
            
            for issue in issues:
                print(f"\n   [{issue['category']}] {issue['message']}")
                
                if issue['details']:
                    # Afficher quelques détails
                    for key, value in list(issue['details'].items())[:3]:
                        if isinstance(value, dict):
                            print(f"      {key}: {len(value)} items")
                        elif isinstance(value, list):
                            print(f"      {key}: {len(value)} items")
                        else:
                            print(f"      {key}: {value}")
        
        print("\n" + "="*70)
        
        if len(self.issues['critical']) == 0:
            print("STATUT: validation OK")
        else:
            print("STATUT: ÉCHEC - problèmes critiques détectés")
        
        print("="*70 + "\n")


def main():
    """Fonction principale"""
    
    parser = argparse.ArgumentParser(
        description="Validation de la qualité des données fact_measures"
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Nombre d\'heures à analyser (défaut: 24)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Mode strict: échoue si warnings (pas seulement critical)'
    )
    
    args = parser.parse_args()
    
    try:
        # Connexion BDD
        db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Créer le validateur
        validator = DataQualityValidator(db, hours=args.hours)
        
        # Exécuter la validation
        validation_ok = validator.run_validation()
        
        # Déterminer le code de sortie
        if not validation_ok:
            print("\nÉCHEC: Problèmes critiques détectés")
            sys.exit(1)
        
        if args.strict and len(validator.issues['warning']) > 0:
            print("\nÉCHEC: Mode strict - warnings détectés")
            sys.exit(1)
        
        print("\nSUCCÈS: Validation complète")
        sys.exit(0)
        
    except Exception as e:
        print(f"\nERREUR D'EXÉCUTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
