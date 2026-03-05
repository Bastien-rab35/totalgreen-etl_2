#!/usr/bin/env python3
"""
Import des données historiques AQICN CSV vers raw_data_lake

CONFIGURATION:
- Villes: Lyon (city_id=3) et Lille (city_id=10) uniquement
- Source: docs/waqi-covid19-airqualitydata-2026.csv
- Période: 2024-01-12 → 2026-03-05
- Format de sortie: Compatible raw_data_lake (format API AQICN)

UTILISATION:
    # Simulation (dry-run)
    python scripts/import_aqicn_historical.py
    
    # Insertion réelle
    python scripts/import_aqicn_historical.py --insert

Ce script convertit les données agrégées journalières du CSV au format
raw_data_lake compatible avec notre base de données.
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.services.database_service import DatabaseService

# ============================================================================
# CONFIGURATION - Lyon et Lille uniquement
# ============================================================================

CITIES_CONFIG = {
    'Lyon': {
        'city_id': 3,  # ID dans dim_city
        'city_name': 'Lyon',
        'station_name': 'Lyon Centre, France',
        'uid': 3028,  # UID station AQICN (Lyon Centre)
        'gps': [45.758, 4.854]
    },
    'Lille': {
        'city_id': 10,  # ID dans dim_city (corrigé: était 6=Nantes)
        'city_name': 'Lille',
        'station_name': 'Lille, France',
        'uid': 8613,  # UID station AQICN (Marcq-en-Baroeul)
        'gps': [50.6292, 3.0573]
    }
}

CSV_FILE = "docs/waqi-covid19-airqualitydata-2026.csv"

# ============================================================================


def calculate_aqi_from_median(species_data: Dict[str, float]) -> int:
    """
    Calcule l'AQI global à partir des valeurs médianes des polluants
    
    Pour simplifier, on prend la valeur maximale parmi les polluants principaux
    """
    pollutants = ['pm25', 'pm10', 'no2', 'o3']
    aqi_values = []
    
    for pol in pollutants:
        if pol in species_data and species_data[pol] is not None:
            aqi_values.append(species_data[pol])
    
    return int(max(aqi_values)) if aqi_values else 0


def parse_csv_to_records(csv_file: Path, start_date: str, end_date: str, cities: List[str]) -> Dict[str, List[Dict]]:
    """
    Parse le CSV AQICN et regroupe les données par ville et par date
    
    Args:
        csv_file: Chemin vers le fichier CSV
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        cities: Liste des villes à extraire
    
    Returns:
        Dictionnaire {ville: [records]}
    """
    
    print(f"\n⏳ Parsing du fichier CSV...")
    
    # Structure: {ville: {date: {specie: median_value}}}
    city_data = defaultdict(lambda: defaultdict(dict))
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    line_count = 0
    matched_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        # Filtrer les lignes de commentaires
        lines = [line for line in f if not line.startswith('#')]
        
        # Revenir au début pour DictReader
        from io import StringIO
        csv_content = StringIO(''.join(lines))
        
        reader = csv.DictReader(csv_content, delimiter=',')
        
        for row in reader:
            line_count += 1
            
            city = row.get('City')
            date_str = row.get('Date')
            specie = row.get('Specie')
            
            # Filtrer par ville
            if city not in cities:
                continue
            
            # Parser la date
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                continue
            
            # Filtrer par période
            if date < start_dt or date > end_dt:
                continue
            
            # Récupérer la valeur médiane
            try:
                median = float(row.get('median', 0))
            except (ValueError, TypeError):
                median = None
            
            # Stocker
            if specie and median is not None:
                city_data[city][date_str][specie] = median
                matched_count += 1
    
    print(f"✅ {line_count:,} lignes traitées")
    print(f"✅ {matched_count:,} données extraites pour {', '.join(cities)}")
    
    # Convertir au format raw_data_lake
    records_by_city = {}
    
    for city in cities:
        if city not in city_data:
            print(f"⚠️  Aucune donnée pour {city}")
            records_by_city[city] = []
            continue
        
        config = CITIES_CONFIG[city]
        records = []
        dates = sorted(city_data[city].keys())
        
        print(f"\n📊 {city}: {len(dates)} jours de données")
        
        for date_str in dates:
            species = city_data[city][date_str]
            
            # Construire l'objet iaqi (Individual Air Quality Index)
            iaqi = {}
            
            # Mapping des noms de polluants
            pollutant_mapping = {
                'pm25': 'pm25',
                'pm10': 'pm10',
                'no2': 'no2',
                'o3': 'o3',
                'so2': 'so2',
                'co': 'co',
                'humidity': 'h',
                'pressure': 'p',
                'temperature': 't',
                'dew': 'dew',
                'wind': 'w'
            }
            
            for spec, value in species.items():
                mapped_name = pollutant_mapping.get(spec, spec)
                iaqi[mapped_name] = {'v': value}
            
            # Calculer l'AQI global
            aqi = calculate_aqi_from_median(species)
            
            # Parser la date
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Construire la réponse au format AQICN API
            raw_data = {
                'status': 'ok',
                'data': {
                    'aqi': aqi,
                    'idx': config['uid'],
                    'city': {
                        'name': config['station_name'],
                        'geo': config['gps'],
                        'url': f"https://aqicn.org/city/@{config['uid']}"
                    },
                    'iaqi': iaqi,
                    'time': {
                        's': date.strftime('%Y-%m-%d %H:%M:%S'),
                        'v': int(date.timestamp()),
                        'tz': '+01:00',
                        'iso': date.strftime('%Y-%m-%dT%H:%M:%S+01:00')
                    },
                    'attributions': [
                        {
                            'name': 'AQICN Historical Data',
                            'url': 'https://aqicn.org/data-platform/'
                        }
                    ]
                }
            }
            
            # Format raw_data_lake
            record = {
                'city_id': config['city_id'],
                'city_name': config['city_name'],
                'source': 'aqicn',
                'raw_data': raw_data,
                'collected_at': date.isoformat(),
                'processed': False,
                'processed_at': None
            }
            
            records.append(record)
        
        records_by_city[city] = records
        
        # Afficher quelques stats
        if records:
            aqi_values = [r['raw_data']['data']['aqi'] for r in records]
            print(f"   Période: {dates[0]} → {dates[-1]}")
            print(f"   AQI moyen: {sum(aqi_values) / len(aqi_values):.1f}")
            print(f"   AQI min: {min(aqi_values)}")
            print(f"   AQI max: {max(aqi_values)}")
    
    return records_by_city


def insert_records(records_by_city: Dict[str, List[Dict]], db: DatabaseService, dry_run: bool = True) -> None:
    """
    Insère les enregistrements dans raw_data_lake
    
    Args:
        records_by_city: Dictionnaire {ville: [records]}
        db: Instance DatabaseService
        dry_run: Si True, simule l'insertion sans la faire réellement
    """
    
    total_records = sum(len(records) for records in records_by_city.values())
    
    print(f"\n{'='*70}")
    print(f"💾 {'SIMULATION' if dry_run else 'INSERTION'} dans raw_data_lake")
    print(f"{'='*70}\n")
    
    print(f"📊 Total: {total_records:,} enregistrements")
    
    for city, records in records_by_city.items():
        print(f"   • {city}: {len(records):,} enregistrements")
    
    if not total_records:
        print("\n❌ Aucun enregistrement à insérer")
        return
    
    # Afficher un exemple
    if total_records > 0:
        first_city = next(iter(records_by_city))
        example = records_by_city[first_city][0]
        
        print(f"\n📋 Exemple d'enregistrement ({first_city}):")
        print(f"   Date: {example['collected_at']}")
        print(f"   AQI: {example['raw_data']['data']['aqi']}")
        print(f"   Polluants: {list(example['raw_data']['data']['iaqi'].keys())}")
    
    if dry_run:
        print(f"\n⚠️  MODE SIMULATION - Aucune insertion réelle")
        print(f"   Pour insérer, relancer avec --insert")
        
        # Sauvegarder des exemples
        for city, records in records_by_city.items():
            if records:
                output_file = Path(__file__).parent / f"{city.lower()}_historical_sample.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(records[:5], f, indent=2, ensure_ascii=False, default=str)
                print(f"   📄 Exemple {city}: {output_file}")
        
        return
    
    # Insertion réelle
    print(f"\n🚀 Insertion en cours...")
    
    batch_size = 100
    total_inserted = 0
    
    for city, records in records_by_city.items():
        print(f"\n   {city}:")
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            try:
                result = db.client.table('raw_data_lake').insert(batch).execute()
                total_inserted += len(batch)
                print(f"      ✅ Batch {i//batch_size + 1}: {len(batch)} enregistrements insérés")
            except Exception as e:
                print(f"      ❌ Erreur batch {i//batch_size + 1}: {e}")
                # Essayer un par un pour identifier les problèmes
                for j, record in enumerate(batch):
                    try:
                        db.client.table('raw_data_lake').insert([record]).execute()
                        total_inserted += 1
                    except Exception as e2:
                        print(f"         ❌ Record {i+j} ({record['collected_at']}): {e2}")
    
    print(f"\n✅ Total inséré: {total_inserted:,}/{total_records:,} enregistrements")


def main():
    """Fonction principale"""
    
    print("\n" + "="*70)
    print("📥 Import données historiques AQICN CSV → raw_data_lake")
    print("="*70)
    
    csv_path = Path(CSV_FILE)
    
    if not csv_path.exists():
        print(f"\n❌ Fichier non trouvé: {csv_path}")
        print(f"\n💡 Assurez-vous que le fichier CSV AQICN est présent dans docs/")
        return
    
    print(f"\n✅ Fichier CSV: {csv_path}")
    print(f"   Taille: {csv_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Période à extraire
    start_date = "2024-01-12"
    end_date = "2026-03-05"
    
    print(f"\n📅 Période: {start_date} → {end_date}")
    
    # Villes à extraire - LYON ET LILLE UNIQUEMENT
    # (city_id: Lyon=3, Lille=10)
    cities = ['Lyon', 'Lille']
    print(f"🏙️  Villes: {', '.join(cities)}")
    
    # Parser le CSV
    records_by_city = parse_csv_to_records(csv_path, start_date, end_date, cities)
    
    # Connexion BDD
    db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # Mode dry-run par défaut
    dry_run = '--insert' not in sys.argv
    
    # Insérer
    insert_records(records_by_city, db, dry_run=dry_run)
    
    print(f"\n{'='*70}")
    
    if dry_run:
        print("ℹ️  Pour effectuer l'insertion réelle:")
        print("   python scripts/import_aqicn_historical.py --insert")
    else:
        print("✅ Import terminé !")
        print("\n📋 Prochaines étapes:")
        print("   1. Transformer les données: python src/etl_transform_to_db.py")
        print("   2. Vérifier: python scripts/check_lyon_aqi.py")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
