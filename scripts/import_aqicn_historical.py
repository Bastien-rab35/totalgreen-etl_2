#!/usr/bin/env python3
"""
Import des donnees historiques AQICN CSV vers raw_data_lake.

Points clefs:
- Lit un CSV WAQI historique (ex: waqi-covid19-airqualitydata-2026Q2.csv)
- Construit un payload compatible avec le format AQICN deja utilise dans le projet
- Peut inserer uniquement les jours/villes manquants (mode par defaut)

Usage:
  # Simulation (par defaut): affiche ce qui serait insere
  python scripts/import_aqicn_historical.py --csv waqi-covid19-airqualitydata-2026Q2.csv --start-date 2026-03-26 --end-date 2026-04-15

  # Insertion reelle
  python scripts/import_aqicn_historical.py --csv waqi-covid19-airqualitydata-2026Q2.csv --start-date 2026-03-26 --end-date 2026-04-15 --insert

  # Forcer l'insertion de toutes les lignes CSV (sans filtrer les manquants)
  python scripts/import_aqicn_historical.py --csv waqi-covid19-airqualitydata-2026Q2.csv --start-date 2026-03-26 --end-date 2026-04-15 --insert --all
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, time, timezone
from io import StringIO
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.services.database_service import DatabaseService

DEFAULT_CSV = "waqi-covid19-airqualitydata-2026Q2.csv"
DEFAULT_START_DATE = "2026-03-26"

POLLUTANT_MAPPING = {
    "pm25": "pm25",
    "pm10": "pm10",
    "no2": "no2",
    "o3": "o3",
    "so2": "so2",
    "co": "co",
    "humidity": "h",
    "pressure": "p",
    "temperature": "t",
    "dew": "dew",
    "wind": "w",
}


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_cities_config() -> Dict[str, Dict]:
    """Charge les villes depuis data/cities_reference.json."""
    ref_path = Path(__file__).resolve().parent.parent / "data" / "cities_reference.json"

    with open(ref_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    config: Dict[str, Dict] = {}
    for row in rows:
        name = row.get("name")
        city_id = row.get("id")
        lat = row.get("latitude")
        lon = row.get("longitude")
        station = row.get("aqi_station")

        if not name or city_id is None:
            continue

        config[name] = {
            "city_id": city_id,
            "city_name": name,
            "station_name": f"{name}, France",
            "uid": int(city_id),
            "gps": [lat, lon] if lat is not None and lon is not None else [],
            "station_path": station or name.lower(),
        }

    return config


def calculate_aqi_from_median(species_data: Dict[str, float]) -> int:
    """Approximation AQI globale via le max des polluants principaux."""
    pollutants = ["pm25", "pm10", "no2", "o3"]
    values = []

    for pol in pollutants:
        val = species_data.get(pol)
        if val is not None:
            values.append(val)

    if not values:
        return 0

    return int(round(max(values)))


def parse_csv_to_daily_species(
    csv_file: Path,
    start_date: date,
    end_date: date,
    cities: List[str],
) -> Dict[str, Dict[date, Dict[str, float]]]:
    """
    Parse le CSV et retourne city -> day -> species medianes.
    """
    city_lookup = {c.lower(): c for c in cities}
    city_data: Dict[str, Dict[date, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))

    line_count = 0
    matched_count = 0

    with open(csv_file, "r", encoding="utf-8") as f:
        filtered_lines = [line for line in f if not line.startswith("#")]
        reader = csv.DictReader(StringIO("".join(filtered_lines)), delimiter=",")

        for row in reader:
            line_count += 1

            raw_city = (row.get("City") or "").strip()
            city = city_lookup.get(raw_city.lower())
            if not city:
                continue

            date_str = (row.get("Date") or "").strip()
            try:
                day = parse_iso_date(date_str)
            except (TypeError, ValueError):
                continue

            if day < start_date or day > end_date:
                continue

            specie = (row.get("Specie") or "").strip().lower()
            if not specie:
                continue

            try:
                median = float(row.get("median"))
            except (TypeError, ValueError):
                continue

            city_data[city][day][specie] = median
            matched_count += 1

    print(f"Lignes CSV lues: {line_count:,}")
    print(f"Lignes retenues (villes/periode): {matched_count:,}")

    return city_data


def build_raw_record(city_cfg: Dict, day: date, species: Dict[str, float]) -> Dict:
    """Construit un enregistrement au format raw_data_lake attendu."""
    ts = datetime.combine(day, time.min, tzinfo=timezone.utc)

    iaqi = {}
    for spec, value in species.items():
        mapped = POLLUTANT_MAPPING.get(spec, spec)
        iaqi[mapped] = {"v": value}

    aqi = calculate_aqi_from_median(species)

    raw_data = {
        "status": "ok",
        "data": {
            "aqi": aqi,
            "idx": city_cfg["uid"],
            "city": {
                "name": city_cfg["station_name"],
                "geo": city_cfg["gps"],
                "url": f"https://aqicn.org/city/{city_cfg['station_path']}",
            },
            "iaqi": iaqi,
            "time": {
                "s": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "v": int(ts.timestamp()),
                "tz": "+00:00",
                "iso": ts.isoformat(),
            },
            "attributions": [
                {
                    "name": "AQICN Historical Data",
                    "url": "https://aqicn.org/data-platform/",
                }
            ],
        },
    }

    return {
        "city_id": city_cfg["city_id"],
        "city_name": city_cfg["city_name"],
        "source": "aqicn",
        "raw_data": raw_data,
        "collected_at": ts.isoformat(),
        "processed": False,
        "processed_at": None,
    }


def convert_to_records(
    city_data: Dict[str, Dict[date, Dict[str, float]]],
    cities_config: Dict[str, Dict],
) -> Dict[str, List[Dict]]:
    """Convertit les medianes journalieres en enregistrements raw_data_lake."""
    records_by_city: Dict[str, List[Dict]] = {}

    for city_name, days_data in city_data.items():
        cfg = cities_config[city_name]
        records: List[Dict] = []

        for day in sorted(days_data.keys()):
            records.append(build_raw_record(cfg, day, days_data[day]))

        records_by_city[city_name] = records

    return records_by_city


def fetch_existing_city_days(db: DatabaseService, start_date: date, end_date: date) -> Set[Tuple[str, date]]:
    """Recupere les couples (city_name, day) deja presents en source aqicn."""
    existing: Set[Tuple[str, date]] = set()

    start_ts = datetime.combine(start_date, time.min, tzinfo=timezone.utc).isoformat()
    end_ts = datetime.combine(end_date, time.max, tzinfo=timezone.utc).isoformat()

    page_size = 1000
    offset = 0

    while True:
        response = (
            db.client.table("raw_data_lake")
            .select("city_name,collected_at")
            .eq("source", "aqicn")
            .gte("collected_at", start_ts)
            .lte("collected_at", end_ts)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        rows = response.data or []
        if not rows:
            break

        for row in rows:
            city_name = row.get("city_name")
            collected_at = row.get("collected_at")
            if not city_name or not collected_at:
                continue

            try:
                day = datetime.fromisoformat(collected_at.replace("Z", "+00:00")).date()
            except ValueError:
                continue

            existing.add((city_name, day))

        if len(rows) < page_size:
            break

        offset += page_size

    return existing


def filter_missing_records(
    records_by_city: Dict[str, List[Dict]],
    existing_city_days: Set[Tuple[str, date]],
) -> Tuple[Dict[str, List[Dict]], int]:
    """Conserve uniquement les jours/villes absents de raw_data_lake."""
    filtered: Dict[str, List[Dict]] = {}
    skipped = 0

    for city_name, records in records_by_city.items():
        kept: List[Dict] = []

        for record in records:
            day = datetime.fromisoformat(record["collected_at"].replace("Z", "+00:00")).date()
            if (record["city_name"], day) in existing_city_days:
                skipped += 1
                continue
            kept.append(record)

        filtered[city_name] = kept

    return filtered, skipped


def insert_records(
    records_by_city: Dict[str, List[Dict]],
    db: DatabaseService,
    dry_run: bool,
    batch_size: int,
) -> int:
    """Insere les enregistrements dans raw_data_lake."""
    total_records = sum(len(v) for v in records_by_city.values())
    print(f"Total enregistrements a inserer: {total_records:,}")

    for city, rows in records_by_city.items():
        print(f"- {city}: {len(rows):,}")

    if total_records == 0:
        return 0

    if dry_run:
        print("Mode simulation actif (--insert absent): aucune ecriture en base.")
        return 0

    inserted = 0

    for city_name, rows in records_by_city.items():
        if not rows:
            continue

        print(f"Insertion {city_name}...")
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            db.client.table("raw_data_lake").insert(batch).execute()
            inserted += len(batch)

    return inserted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import historique AQICN CSV -> raw_data_lake")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Chemin du CSV historique")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Date debut YYYY-MM-DD")
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Date fin YYYY-MM-DD",
    )
    parser.add_argument(
        "--cities",
        default="",
        help="Liste de villes separees par virgule (defaut: toutes les villes du referentiel)",
    )
    parser.add_argument("--insert", action="store_true", help="Effectuer l'insertion reelle")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ne pas filtrer sur les jours deja presents en base",
    )
    parser.add_argument("--batch-size", type=int, default=200, help="Taille de batch d'insertion")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    start_date = parse_iso_date(args.start_date)
    end_date = parse_iso_date(args.end_date)

    if end_date < start_date:
        raise ValueError("--end-date doit etre >= --start-date")

    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = Path(__file__).resolve().parent.parent / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable: {csv_path}")

    cities_config = load_cities_config()

    if args.cities.strip():
        requested = [c.strip() for c in args.cities.split(",") if c.strip()]
        missing = [c for c in requested if c not in cities_config]
        if missing:
            raise ValueError(f"Villes inconnues dans --cities: {', '.join(missing)}")
        selected_cities = requested
    else:
        selected_cities = list(cities_config.keys())

    print("=" * 70)
    print("Import historique AQICN CSV -> raw_data_lake")
    print("=" * 70)
    print(f"CSV: {csv_path}")
    print(f"Periode: {start_date} -> {end_date}")
    print(f"Villes: {', '.join(selected_cities)}")
    print(f"Mode: {'INSERT' if args.insert else 'DRY-RUN'}")
    print(f"Filtre manquants: {'NON' if args.all else 'OUI'}")

    city_data = parse_csv_to_daily_species(csv_path, start_date, end_date, selected_cities)
    records_by_city = convert_to_records(city_data, cities_config)

    db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    if not args.all:
        existing = fetch_existing_city_days(db, start_date, end_date)
        records_by_city, skipped = filter_missing_records(records_by_city, existing)
        print(f"Jours/villes deja presents ignores: {skipped:,}")

    inserted = insert_records(records_by_city, db, dry_run=not args.insert, batch_size=args.batch_size)

    if args.insert:
        print(f"Insertion terminee: {inserted:,} enregistrements ajoutes.")
        print("Etape suivante: python scripts/process_all_remaining.py")


if __name__ == "__main__":
    main()
