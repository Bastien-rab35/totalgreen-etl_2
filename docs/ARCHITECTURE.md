# Architecture Technique - TotalGreen ETL

Documentation technique du projet de surveillance environnementale.

---

## Architecture Globale

### Modèle en Étoile (Star Schema)

Le projet utilise un **Data Warehouse OLAP** avec modèle dimensionnel en étoile pour optimiser les analyses multidimensionnelles.

```
        dim_time
            |
            |
dim_city -- fact_measures -- dim_weather_condition
            |
            |
    dim_air_quality_level
```

### Pipeline ETL 3 Couches

```
APIs (OpenWeather + AQICN)
    ↓ Extract
Data Lake (JSONB - raw_data_lake)
    ↓ Transform
Data Warehouse (Star Schema - fact_measures)
```

---

## Composants

### 1. Data Lake (Couche Bronze)

**Table : `raw_data_lake`**
- Stockage JSONB des données brutes
- Traçabilité complète (source, timestamp)
- Pas de transformation
- Index GIN pour requêtes JSON rapides

```sql
CREATE TABLE raw_data_lake (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER,
    source VARCHAR(50),        -- 'openweather' | 'aqicn'
    raw_data JSONB,
    collected_at TIMESTAMP WITH TIME ZONE,
    processed BOOLEAN DEFAULT FALSE
);
```

### 2. Data Warehouse (Couche Or)

**Dimensions :**
- `dim_time` : ~26,000 périodes (2024-2027, granularité horaire)
- `dim_city` : 10 villes françaises avec métadonnées géographiques
- `dim_weather_condition` : 40+ conditions météo OpenWeather
- `dim_air_quality_level` : 6 niveaux EPA (Good → Hazardous)

**Table de faits :**
- `fact_measures` : Mesures environnementales agrégées
  - Métriques météo : température, humidité, pression, vent, nuages
  - Métriques AQI : PM2.5, PM10, NO2, O3, SO2, CO
  - Références dimensions via FK
  - Traçabilité vers data lake (raw_weather_id, raw_aqi_id)

---

## Pipeline ETL

### Extract (etl_extract_to_lake.py)

```python
APIs → Data Lake (JSONB)
```

- Collecte depuis OpenWeather API (météo)
- Collecte depuis AQICN API (qualité air)
- Stockage brut sans transformation
- Exécution : Toutes les heures (GitHub Actions)

### Transform (etl_transform_to_db.py)

```python
Data Lake → Data Warehouse (Star Schema)
```

- Lecture données non traitées (processed=false)
- Groupement par (city_id, timestamp arrondi à l'heure)
- Fusion météo + AQI
- **Lookup dimensions** :
  - `time_id` depuis `dim_time`
  - `weather_condition_id` depuis `dim_weather_condition`
  - `aqi_level_id` via fonction `get_aqi_level_id()`
- Insertion dans `fact_measures`
- Marquage traité (processed=true)
- Exécution : Toutes les heures (GitHub Actions)

### Stratégie Anti-Perte

- **Mesures complètes** : météo + AQI fusionnés
- **Mesures partielles** : une seule source (stockées quand même)
- **Mesures orphelines** : >2h d'âge traitées immédiatement
- **Garantie 0% perte** : toutes les données collectées sont chargées

---

## Sécurité et Conformité

### RGPD

- Hébergement UE (Supabase eu-central-1)
- Aucune donnée personnelle collectée
- Données agrégées par ville (pas de géolocalisation précise)
- Conservation limitée (30 jours data lake, 1 an warehouse)

### Sécurité

- Variables d'environnement (.env non versionné)
- Connexions HTTPS/TLS
- Clés API rotatives
- Logs de traçabilité (etl_logs)

### Validation Qualité

Script Python `validate_data_quality.py` :
- 5 niveaux de validation
- Exécution automatisée (2×/jour via GitHub Actions)
- Détection doublons, incohérences, outliers
- Exit codes pour intégration CI/CD

---

## Performances

### Optimisations

- **Indexes** :
  - GIN sur `raw_data.jsonb` (data lake)
  - B-Tree sur FK dimensions (fact_measures)
  - Composite sur (time_id, city_id)

- **Requêtes OLAP** :
  - Pré-agrégations via dimensions
  - Vues matérialisées pour analyses fréquentes
  - Partitionnement temporel possible

### Métriques

- Collecte : ~20s pour 10 villes (2 APIs × 10 villes)
- Transform : ~3s pour 100 entrées
- Stockage : ~500 Ko/jour

---

## Technologies

- **Base de données** : PostgreSQL 15 (Supabase EU Francfort)
- **Langage** : Python 3.12
- **Librairies** : requests, supabase-py, numpy, python-dotenv
- **APIs externes** : OpenWeather (météo) + AQICN (qualité air)
- **Orchestration** : GitHub Actions (CRON 3 workflows)
- **Hébergement** : Supabase eu-central-1 (conformité RGPD)
- **Validation** : Script Python 5 niveaux (détection anomalies)

---

## Références

- [Schema SQL complet](../sql/star_schema.sql)
- [Requêtes OLAP](../sql/queries_olap.sql)
- [Pipeline Extract](../src/etl_extract_to_lake.py)
- [Pipeline Transform](../src/etl_transform_to_db.py)

---

**Version** : 2.0 (Data Warehouse en étoile)  
**Dernière mise à jour** : 2026-02-09
