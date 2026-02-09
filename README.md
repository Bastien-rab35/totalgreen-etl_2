# TotalGreen - Data Warehouse Environnemental 

**Pipeline ETL automatisé** pour la collecte et l'analyse de données environnementales sur les 10 plus grandes villes métropolitaines françaises.

## Vue d'ensemble

Pipeline de données **production-ready** avec :
- **Collecte automatisée** : APIs OpenWeather + AQICN (toutes les heures via GitHub Actions)
- **Data Lake JSONB** : Stockage brut des données avec versioning
- **Data Warehouse** : Modèle en **étoile** optimisé pour l'analyse
- **ML Anomaly Detection** : Isolation Forest + règles métier + analyse statistique
- **Conformité RGPD** : Hébergement EU (Francfort) avec sécurité renforcée

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              PIPELINE 1 : EXTRACTION (toutes les heures)     │
│  APIs (OpenWeather + AQICN) → Data Lake (JSONB) → Lake      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         PIPELINE 2 : TRANSFORMATION (toutes les heures)      │
│  Data Lake → ML Anomaly Detection ⚡ → Star Schema ⭐        │
└─────────────────────────────────────────────────────────────┘
```

### Structure du projet

```
MSPR 1/
├── data/
│   └── cities_reference.json     # Référentiel des 10 villes
├── docs/                         # 📚 Documentation
│   ├── README.md                       # Index de la documentation
│   ├── ARCHITECTURE.md                 # Architecture technique détaillée
│   ├── ANOMALY_DETECTION.md            # 🤖 Guide ML Anomaly Detection
│   ├── SECURITE.md                     # RGPD et sécurité
│   └── archive/                        # Anciens documents techniques
├── logs/                         # Logs d'exécution
├── sql/
│   ├── star_schema.sql                # ⭐ Schéma en étoile (Data Warehouse)
│   ├── anomaly_detection_schema.sql   # Schéma détection d'anomalies ML
│   ├── anomaly_functions.sql          # Fonctions SQL (get_city_stats, get_anomaly_summary)
│   └── archive/                       # Anciens scripts SQL
├── scripts/
│   ├── check_bdd_status.py      # Vérification BDD
│   ├── check_data_lake.py       # Vérification Data Lake
│   └── archive/                 # Scripts de migration
├── src/
│   ├── services/
│   │   ├── weather_service.py            # API OpenWeather
│   │   ├── air_quality_service.py        # API AQICN
│   │   ├── data_lake_service.py          # Gestion Data Lake
│   │   ├── database_service.py           # Supabase + Star Schema
│   │   └── anomaly_detection_service.py  # ML Anomaly Detection (Isolation Forest)
│   ├── config.py                     # Configuration centralisée
│   ├── etl_extract_to_lake.py       # Pipeline Extract → Lake
│   └── etl_transform_to_db.py       # Pipeline Lake → Warehouse
├── .github/workflows/
│   ├── etl-extract.yml          # Automatisation extraction
│   └── etl-transform.yml        # Automatisation transformation
├── requirements.txt             # Dépendances Python
└── README.md                    # Ce fichier
```

## 🚀 Installation rapide

### Prérequis
- **Python 3.12+**
- **Compte Supabase** (région EU : `eu-central-1` Francfort)
- **Clés API** : OpenWeather + AQICN

### 1. Installation

```bash
# Cloner le projet
git clone https://github.com/Bastien-rab35/totalgreen-etl.git
cd totalgreen-etl

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Créer le fichier .env avec vos clés
cp .env.example .env
```

Éditez `.env` :
```env
OPENWEATHER_API_KEY=votre_clé
AQICN_API_KEY=votre_clé
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=votre_service_key
```

### 3. Déploiement Data Warehouse

Dans l'éditeur SQL Supabase, exécutez **dans cet ordre** :

```sql
-- 1. Créer le schéma en étoile (⭐ Data Warehouse)
\i sql/star_schema.sql

-- 2. Créer la table dim_date (architecture simplifiée)
\i sql/create_dim_date.sql

-- 3. ⚠️ IMPORTANT : Nettoyer l'ancienne architecture dim_time
--    (si vous migrez depuis une ancienne version)
\i sql/cleanup_dim_time.sql
```

Cela crée :
- **4 tables de dimensions** : dim_date, dim_city, dim_weather_condition, dim_air_quality_level
- **1 table de faits** : fact_measures (avec `captured_at` et `capture_date`)
- **~1 460 jours** dans dim_date (couvre 4 ans : 2024-2027)

## Utilisation

### Automatisation (Production)

Le projet utilise **GitHub Actions** :
- **Extract Pipeline** : Toutes les heures → Data Lake JSONB
- **Transform Pipeline** : Toutes les heures → Star Schema

Voir [.github/workflows/](.github/workflows/)

### Tests manuels

```bash
# Pipeline 1 : Extraction vers Data Lake
python src/etl_extract_to_lake.py

# Pipeline 2 : Transformation vers Data Warehouse
python src/etl_transform_to_db.py

# Vérifier le statut
python scripts/check_bdd_status.py
python scripts/check_data_lake.py
```## 🗄️ Modèle de données (Star Schema ⭐)

Le Data Warehouse utilise un **schéma en étoile** optimisé pour l'analyse avec une architecture temporelle simplifiée :

### Table de faits
- **`fact_measures`** : Mesures environnementales horaires
  - Métriques météo : température, pression, humidité, vent, UV, visibilité
  - Métriques qualité de l'air : AQI, PM2.5, PM10, NO2, O3, SO2, CO
  - **Timestamp natif** : `captured_at` (TIMESTAMP exact de la mesure)
  - Clés étrangères : `capture_date`, `city_id`, `weather_condition_id`, `aqi_level_id`

### Tables de dimensions
- **`dim_date`** : Dimension temporelle **simplifiée** ✨
  - Clé naturelle : `date_value` (DATE - format YYYY-MM-DD)
  - Attributs : jour, jour_semaine, semaine, mois, trimestre, année, saison, weekend
  - ~1 460 jours (4 ans : 2024-2027)
  - **Avantage** : Pas de lookup complexe, jointures directes avec `DATE(captured_at)`
  
- **`dim_city`** : Dimension géographique
  - 10 villes françaises avec coordonnées GPS
  
- **`dim_weather_condition`** : Conditions météo
  - 40+ conditions (Clear, Clouds, Rain, Snow, etc.)
  
- **`dim_air_quality_level`** : Niveaux de qualité de l'air
  - 6 niveaux (Good, Fair, Moderate, Poor, Very Poor, Severe)

### Avantages
✅ **Architecture temporelle simplifiée** : `captured_at` + `dim_date` au lieu de `time_id` artificiel
✅ Requêtes optimisées pour l'analyse (pas de conversion date/heure)
✅ Agrégations temporelles rapides et intuitives
✅ Jointures simplifiées : `fact_measures.capture_date = dim_date.date_value`
✅ Évolutivité garantie

## Data Lake

### Table `lake`
- Stockage **JSONB** des données brutes API
- Colonnes : `city_name`, `source`, `data_type`, `raw_data`, `captured_at`, `processed`
- Permet : audit, retraitement, versioning des données

### Workflow
1. **Extraction** : API → Data Lake (`processed=false`)
2. **Transformation** : Data Lake → Validation → Star Schema
3. **Marquage** : `processed=true` après insertion réussie

## ML Anomaly Detection

**Système de détection d'anomalies multi-niveaux** pour garantir la qualité des données.

### 3 niveaux de détection

1. **Règles métier** (Business Rules)
   - Limites physiques : température -50°C à 60°C, humidité 0-100%, pression 870-1084 hPa
   - AQI 0-500, PM2.5/PM10 0-1000 µg/m³
   - Validation immédiate avant insertion

2. **Analyse statistique** (Z-score)
   - Calcul sur historique 30 jours par ville
   - Seuils : low (2σ), medium (2.5σ), high (3σ), critical (4σ)
   - Détection des valeurs aberrantes univariées

3. **ML Isolation Forest** (Multivarié)
   - Entraînement automatique sur 5000 mesures historiques (minimum 100)
   - Contamination : 5% (détecte top 5% anomalies)
   - Analyse multivariée sur [temp, humidity, pressure, aqi_index, pm25, pm10]

### Tables & Colonnes

**Table `anomalies`** : Stockage des anomalies détectées
```sql
id, city_id, measure_id, detected_at, anomaly_type, severity, 
field_name, actual_value, expected_range, anomaly_score
```

**Table `fact_measures`** : Flags ML
- `is_anomaly` : BOOLEAN (TRUE si anomalie détectée)
- `anomaly_score` : NUMERIC (score ML entre 0 et 1)

**Vues** :
- `v_anomalies_summary` : Résumé par ville/type/sévérité
- `v_critical_anomalies` : Anomalies critiques des 7 derniers jours

### Workflow automatique

1. **Entraînement** : Modèle ML entraîné sur mesures historiques propres (non-anomalies)
2. **Détection** : 3 niveaux appliqués avant insertion dans `fact_measures`
3. **Action** :
   - Anomalies **critiques** (>4σ ou hors limites) → Rejetées (non insérées)
   - Anomalies **low/medium/high** → Flaggées (`is_anomaly=TRUE`) et stockées dans `anomalies`
4. **Traçabilité** : Toutes les anomalies loggées avec détails (champ, valeur, seuil)

### Fonctions SQL

**`get_city_stats(p_city_name TEXT, p_days INTEGER)`** : Statistiques par ville
```sql
SELECT * FROM get_city_stats('Paris', 30);
-- Retourne : mean/std/min/max pour temperature, humidity, pressure, aqi_index
```

**`get_anomaly_summary(p_days INTEGER)`** : Agrégation des anomalies
```sql
SELECT * FROM get_anomaly_summary(7);
-- Retourne : count par ville/type/severity sur les 7 derniers jours
```

### Configuration

**Fichier** : `src/services/anomaly_detection_service.py`

```python
# Seuils Z-score
Z_SCORE_THRESHOLD = {
    'low': 2.0, 'medium': 2.5, 'high': 3.0, 'critical': 4.0
}

# ML Isolation Forest
IsolationForest(contamination=0.05, random_state=42)

# Données historiques pour entraînement
MIN_TRAINING_SAMPLES = 100  # Minimum pour activer ML
MAX_TRAINING_SAMPLES = 5000 # Limite pour performance
```

📖 **Guide complet** : [docs/ANOMALY_DETECTION.md](docs/ANOMALY_DETECTION.md)

## 🔒 Sécurité et RGPD

✅ **Conformité RGPD garantie**
- Hébergement Supabase : **eu-central-1** (Francfort, Allemagne)
- Pas de données personnelles collectées
- Retention policy : 3 ans (dim_time)

✅ **Sécurité des secrets**
- Clés API dans `.env` (jamais commitées)
- `.gitignore` configuré
- GitHub Secrets pour CI/CD

✅ **Contrôle d'accès**
- Service Key Supabase avec RLS
- API rate limiting activé

📖 Documentation complète : [docs/SECURITE.md](docs/SECURITE.md)

## Monitoring

### Vérifications système

```bash
# Statut de la base de données
python scripts/check_bdd_status.py

# Statut du data lake
python scripts/check_data_lake.py
```

### Requêtes utiles

```sql
-- Dernières mesures (avec timestamp exact)
SELECT 
  fm.captured_at,
  dd.date_value,
  dc.city_name,
  fm.temperature,
  fm.aqi,
  aq.level_name as air_quality
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
JOIN dim_city dc ON fm.city_id = dc.city_id
LEFT JOIN dim_air_quality_level aq ON fm.aqi_level_id = aq.aqi_level_id
ORDER BY fm.captured_at DESC
LIMIT 10;

-- Statistiques par ville (agrégation par jour)
SELECT 
  dc.city_name,
  COUNT(*) as nb_mesures,
  ROUND(AVG(fm.temperature), 1) as temp_moyenne,
  ROUND(AVG(fm.aqi), 0) as aqi_moyen
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dd ON fm.capture_date = dd.date_value
WHERE dd.date_value >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dc.city_name
ORDER BY dc.city_name;

-- Agrégation par jour de la semaine
SELECT 
  dd.day_name,
  ROUND(AVG(fm.temperature), 1) as temp_moyenne
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
WHERE dd.date_value >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY dd.day_name, dd.day_of_week
ORDER BY dd.day_of_week;

-- Monitoring des anomalies (7 derniers jours)
SELECT * FROM get_anomaly_summary(7);

-- Statistiques par ville (30 derniers jours)
SELECT * FROM get_city_stats('Paris', 30);

-- Anomalies critiques récentes
SELECT * FROM v_critical_anomalies;

-- Mesures flaggées comme anomalies
SELECT 
  dc.name AS city,
  fm.captured_at,
  dd.date_value,
  fm.temperature,
  fm.aqi_index,
  fm.anomaly_score,
  a.anomaly_type,
  a.severity
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dd ON fm.capture_date = dd.date_value
LEFT JOIN anomalies a ON fm.measure_id = a.measure_id
WHERE fm.is_anomaly = TRUE
ORDER BY fm.captured_at DESC, fm.anomaly_score DESC
LIMIT 20;
```

## Performance & Quotas

### Quotas API (plan gratuit)
- **OpenWeather** : 1000 appels/jour
  - Utilisation : 240 appels/jour (10 villes × 24h)
  - Taux : **24%** ✅
  
- **AQICN** : Varie selon le plan
  - Utilisation : 240 appels/jour

### Métriques du Data Warehouse
- **dim_date** : ~1 460 jours (4 ans : 2024-2027)
- **dim_city** : 10 villes
- **dim_weather_condition** : 40+ conditions
- **dim_air_quality_level** : 6 niveaux
- **fact_measures** : Croissance ~240 mesures/jour (avec timestamps natifs)

## 📚 Documentation

- **[docs/README.md](docs/README.md)** - Index de la documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture technique détaillée
- **[docs/ANOMALY_DETECTION.md](docs/ANOMALY_DETECTION.md)** - 🤖 Guide ML Anomaly Detection
- **[docs/SECURITE.md](docs/SECURITE.md)** - Sécurité et RGPD
- **[docs/archive/](docs/archive/)** - Anciens documents techniques

## 🎓 Livrables du projet

### ✅ Phase 1 : Architecture & Data Lake
- Data Lake JSONB avec versioning
- Pipeline Extract → Lake automatisé

### ✅ Phase 2 : Data Warehouse 
- Modèle en étoile (5 tables)
- Pipeline Transform → Warehouse
- Migration ~500 mesures historiques

### ✅ Phase 3 : Automatisation & Production
- GitHub Actions (2 workflows)
- Monitoring et logs
- Conformité RGPD

### ✅ Phase 4 : ML & Qualité des Données
- **ML Anomaly Detection** 
  - Isolation Forest opérationnel
  - Règles métier + analyse statistique (Z-score)
  - 3 niveaux de détection actifs
  - Tables `anomalies` + flags `fact_measures`

## Dépannage

### Erreur de connexion Supabase
```bash
# Vérifier les variables d'environnement
cat .env | grep SUPABASE

# Tester la connexion
python scripts/check_bdd_status.py
```

### Erreur API
```bash
# Vérifier les clés API
cat .env | grep API_KEY

# Tester manuellement
python src/etl_extract_to_lake.py
```

### Data Lake vide
```bash
# Vérifier le contenu
python scripts/check_data_lake.py

# Lancer l'extraction
python src/etl_extract_to_lake.py
```

## 🔗 Liens utiles

- **GitHub** : [Bastien-rab35/totalgreen-etl](https://github.com/Bastien-rab35/totalgreen-etl)
- **Supabase** : [uqntmecpgswkdchcfwxe.supabase.co](https://uqntmecpgswkdchcfwxe.supabase.co)
- **OpenWeather API** : [openweathermap.org](https://openweathermap.org)
- **AQICN API** : [aqicn.org](https://aqicn.org)

---

**📅 Créé** : Janvier 2026  
**🏷️ Version** : 2.0.0 (Star Schema + ML)  
**✅ Conformité** : RGPD (hébergement EU)  
**⚡ Automatisation** : GitHub Actions  
