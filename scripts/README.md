# Scripts ETL - TotalGreen

Scripts Python pour les pipelines de données du projet.

## Scripts de production

### Import et traitement ETL
- **`import_aqicn_historical.py`** - Import de données historiques depuis CSV AQICN
  - Parse le fichier CSV AQICN (format agrégats journaliers)
  - Insertion dans raw_data_lake au format API AQICN
  - Support Lyon Centre (UID 3028) et Lille

- **`process_all_remaining.py`** - Traitement ETL de toutes les données non traitées
  - Boucle sur le pipeline Transform (etl_transform_to_db)
  - Traite itérativement jusqu'à processed=true
  - Utilisé après imports CSV massifs
### Validation et qualité des données
- **`validate_data_quality.py`** - Validation intégrité et qualité des données
  - Vérifie l'intégrité structurelle (NULL, doublons, FK)
  - Cohérence temporelle (gaps, dates futures)
  - Limites physiques (business rules)
  - Couverture des données (10 villes)
  - Détection outliers statistiques (>3σ)
  - Conçu pour GitHub Actions (exit codes 0/1/2)
## Dossiers

### `archive/`
Scripts de déploiement historiques (déjà exécutés).

### `temp/` (non versionné)
Scripts de vérification, diagnostic et maintenance.
Non pushés sur GitHub (voir `.gitignore`).

## Utilisation

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Import de données historiques CSV
python scripts/import_aqicn_historical.py --insert

# Traiter les données non traitées
python scripts/process_all_remaining.py

# Valider la qualité des données (24h)
python scripts/validate_data_quality.py

# Valider avec période spécifique
python scripts/validate_data_quality.py --hours 48 --strict
```

## Organisation

Les scripts sont organisés pour ne versioner que le code de production :
- **scripts/** : Scripts ETL de production uniquement
- **scripts/archive/** : Scripts de déploiement exécutés une fois
- **scripts/temp/** : Scripts temporaires (exclus Git)

Pour les vérifications/diagnostics, utiliser les scripts dans `temp/` :
- check_bdd_status.py - Vérification état BDD
- verify_star_schema.py - Vérification modèle en étoile
- audit_fact_measures.py - Audit complet intégrité
- etc.

Note : `validate_data_quality.py` est dans scripts/ car utilisé en production (GitHub Actions).

