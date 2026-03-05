# TotalGreen - Data Warehouse Environnemental

Pipeline ETL automatisé pour la collecte et l'analyse de données environnementales (météo + qualité de l'air) sur 10 villes françaises.

## À propos

**Objectif** : Collecte automatisée de données environnementales (météo OpenWeather + qualité de l'air AQICN) avec stockage dans un Data Warehouse optimisé pour l'analyse.

**Villes surveillées** : Paris, Marseille, Lyon, Toulouse, Nice, Nantes, Montpellier, Strasbourg, Bordeaux, Lille

**Fonctionnalités** :
- Collecte horaire automatisée (GitHub Actions)
- Data Lake JSONB pour versioning des données brutes
- Data Warehouse en étoile (Star Schema) pour analyses OLAP
- Détection d'anomalies ML (Isolation Forest + règles métier)
- Validation qualité des données
- Conformité RGPD (hébergement EU Francfort)

---

## 🚀 Quick Start (5 minutes)

### 1. Prérequis
- Python 3.12+
- Compte Supabase (région EU)
- Clés API : OpenWeather + AQICN

### 2. Installation

```bash
# Cloner et installer
git clone https://github.com/Bastien-rab35/totalgreen-etl.git
cd totalgreen-etl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

Créer le fichier `.env` :
```env
OPENWEATHER_API_KEY=votre_clé
AQICN_API_KEY=votre_clé
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=votre_service_key
```

### 4. Déployer le Data Warehouse

Dans l'éditeur SQL Supabase, exécuter dans cet ordre :
```sql
-- 1. Schéma en étoile (tables dimensions + faits)
\i sql/star_schema.sql

-- 2. Table temporelle dim_date (2024-2027)
\i sql/create_dim_date.sql

-- 3. Schéma détection d'anomalies ML
\i sql/anomaly_detection_schema.sql

-- 4. Fonctions SQL analytiques
\i sql/anomaly_functions.sql
```

### 5. Tester le pipeline

```bash
# Pipeline 1 : APIs → Data Lake
python src/etl_extract_to_lake.py

# Pipeline 2 : Data Lake → Data Warehouse
python src/etl_transform_to_db.py

# Vérifier les résultats
python scripts/validate_data_quality.py --hours 24
```

✅ **Installation terminée** ! Le système collecte maintenant les données.

---

## 📋 Guide complet du processus

### Étape 1 : Comprendre l'architecture

Le projet utilise 2 pipelines ETL automatisés :

```
PIPELINE 1 (Extraction - toutes les heures)
APIs → Data Lake JSONB → Fichiers JSON locaux

PIPELINE 2 (Transformation - toutes les heures)  
Data Lake → Validation + ML → Star Schema
```

**Data Lake** (`raw_data_lake`) :
- Stockage JSONB des réponses API brutes
- Colonnes : `city_name`, `source`, `data_type`, `raw_data`, `captured_at`, `processed`
- Permet audit, retraitement et versioning

**Data Warehouse** (Star Schema) :
- `fact_measures` : Mesures environnementales horaires
- `dim_date` : Dimension temporelle (1460 jours)
- `dim_city` : 10 villes françaises
- `dim_weather_condition` : ~40 conditions météo
- `dim_air_quality_level` : 6 niveaux qualité air

### Étape 2 : Configuration initiale

#### A. Créer les comptes API

1. **OpenWeather** : [openweathermap.org/api](https://openweathermap.org/api)
   - Plan gratuit : 1000 appels/jour
   - Récupérer votre API Key

2. **AQICN** : [aqicn.org/data-platform/token](https://aqicn.org/data-platform/token)
   - Plan gratuit disponible
   - Récupérer votre Token

3. **Supabase** : [supabase.com](https://supabase.com)
   - Créer un projet en région `eu-central-1` (Francfort)
   - Récupérer : URL + Service Key (anon key insuffisante)

#### B. Configurer le fichier .env

Créer `.env` à la racine du projet :
```env
# APIs externes
OPENWEATHER_API_KEY=votre_clé_openweather
AQICN_API_KEY=votre_token_aqicn

# Supabase (région EU obligatoire)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **Important** : Utiliser la Service Role Key, pas l'anon key

### Étape 3 : Déployer le schéma de base de données

#### Ordre d'exécution des scripts SQL

Dans l'éditeur SQL Supabase, exécuter dans cet ordre précis :

**1. Star Schema** (`sql/star_schema.sql`)
```sql
-- Crée les tables :
-- - dim_city (10 villes avec coordonnées GPS)
-- - dim_weather_condition (~40 conditions)
-- - dim_air_quality_level (6 niveaux)
-- - fact_measures (mesures environnementales)
-- - raw_data_lake (stockage JSONB)
```

**2. Dimension temporelle** (`sql/create_dim_date.sql`)
```sql
-- Génère ~1460 jours (2024-2027)
-- Attributs : jour, mois, année, saison, weekend, etc.
```

**3. Schéma détection d'anomalies** (`sql/anomaly_detection_schema.sql`)
```sql
-- Crée les tables :
-- - anomalies (stockage des anomalies détectées)
-- - ml_model_metadata (métadonnées des modèles ML)
-- - Ajoute colonnes is_anomaly + anomaly_score à fact_measures
```

**4. Fonctions SQL** (`sql/anomaly_functions.sql`)
```sql
-- Crée les fonctions :
-- - get_city_stats(city_name, days) : statistiques par ville
-- - get_anomaly_summary(days) : résumé des anomalies
-- - Vues : v_anomalies_summary, v_critical_anomalies
```

#### Vérifier le déploiement

```sql
-- Compter les tables
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
-- Attendu : 9 tables

-- Vérifier dim_date
SELECT COUNT(*) FROM dim_date;
-- Attendu : ~1460 jours

-- Vérifier dim_city
SELECT COUNT(*) FROM dim_city;
-- Attendu : 10 villes
```

### Étape 4 : Premier test du pipeline

#### A. Collecte de données (Pipeline 1)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'extraction
python src/etl_extract_to_lake.py
```

**Ce script va** :
1. Charger les 10 villes depuis la BDD
2. Appeler OpenWeather API (10 villes = 10 appels)
3. Appeler AQICN API (10 villes = 10 appels)
4. Stocker les réponses JSON dans `raw_data_lake` avec `processed=false`
5. Sauvegarder les JSON localement dans `src/data/lake/`

**Vérifier les résultats** :
```bash
# Compter les enregistrements dans le Data Lake
python -c "
from src.services.database_service import DatabaseService
from src.config import Config
db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
count = db.client.table('raw_data_lake').select('*', count='exact').execute()
print(f'Enregistrements dans raw_data_lake : {count.count}')
"
```

Attendu : 20 enregistrements (10 villes × 2 sources)

#### B. Transformation des données (Pipeline 2)

```bash
# Lancer la transformation
python src/etl_transform_to_db.py
```

**Ce script va** :
1. Charger les enregistrements `processed=false` du Data Lake
2. Parser les données JSON
3. Appliquer les 3 niveaux de détection d'anomalies :
   - Règles métier (limites physiques)
   - Analyse statistique (Z-score)
   - ML Isolation Forest (si ≥100 données historiques)
4. Insérer dans `fact_measures` (avec flags anomalies)
5. Marquer `processed=true` dans `raw_data_lake`

**Vérifier les résultats** :
```bash
# Compter les mesures insérées
python -c "
from src.services.database_service import DatabaseService
from src.config import Config
db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
count = db.client.table('fact_measures').select('*', count='exact').execute()
print(f'Mesures dans fact_measures : {count.count}')
"
```

Attendu : ~10 mesures (1 par ville si données valides)

### Étape 5 : Import de données historiques (optionnel)

Pour analyser des données passées, vous pouvez importer des fichiers CSV historiques AQICN.

**Configurer le script pour vos villes** :
Éditer `scripts/import_aqicn_historical.py` lignes 145-161 :
```python
cities = [
    {
        'city_id': 3,
        'city_name': 'Lyon',
        'station_uid': '@3028',
        'csv_file': 'path/to/lyon-air-quality.csv'
    },
    {
        'city_id': 10,
        'city_name': 'Lille',
        'station_uid': '@8613',
        'csv_file': 'path/to/lille-air-quality.csv'
    }
]
```

**Lancer l'import** :
```bash
# Mode dry-run (vérifier avant import)
python scripts/import_aqicn_historical.py

# Mode import réel
python scripts/import_aqicn_historical.py --insert
```

**Traiter les données importées** :
```bash
# Traite TOUTES les données non-traitées (processed=false)
python scripts/process_all_remaining.py
```

Ce script boucle jusqu'à ce que toutes les données soient traitées.

### Étape 6 : Validation de la qualité des données

Le projet inclut un script de validation multi-niveaux.

```bash
# Valider les données des dernières 24h
python scripts/validate_data_quality.py --hours 24

# Mode strict (exit code 1 si WARNING)
python scripts/validate_data_quality.py --hours 24 --strict
```

**5 niveaux de validation** :
1. **Structural Integrity** : Détecte NULL, duplicates
2. **Temporal Coherence** : Détecte gaps, future dates, incohérences timestamps
3. **Business Rules** : Vérifie limites physiques (temp, pression, AQI, etc.)
4. **Data Coverage** : Vérifie présence des 10 villes (ou seuil personnalisé)
5. **Statistical Outliers** : Détecte valeurs aberrantes (Z-score > 3σ)

**Exit codes** :
- `0` : Validation réussie (pas d'erreurs)
- `1` : Warnings détectés
- `2` : Erreurs critiques détectées

### Étape 7 : Automatisation avec GitHub Actions

Le projet inclut 3 workflows GitHub Actions :

#### A. Pipeline d'extraction (`.github/workflows/etl-extract.yml`)
- **Déclenchement** : Cron toutes les heures
- **Action** : Collecte données APIs → Data Lake
- **Quota** : 240 appels/jour (10 villes × 24h × 2 APIs)

#### B. Pipeline de transformation (`.github/workflows/etl-transform.yml`)
- **Déclenchement** : Cron toutes les heures
- **Action** : Data Lake → Validation + ML → Data Warehouse
- **Dépendance** : Attend fin d'extraction

#### C. Validation qualité (`.github/workflows/data-quality-validation.yml`)
- **Déclenchement** : Cron toutes les heures (à :15)
- **Action** : Valide données des dernières 24h
- **Report** : GitHub Actions Summary avec détails

**Configuration GitHub Secrets** :
1. Aller dans Settings → Secrets → Actions
2. Créer les secrets :
   - `OPENWEATHER_API_KEY`
   - `AQICN_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

**Activer les workflows** :
1. Pusher le code sur GitHub
2. Aller dans Actions tab
3. Activer les workflows

### Étape 8 : Monitoring et maintenance

#### A. Requêtes SQL utiles

**Dernières mesures** :
```sql
SELECT 
  fm.captured_at,
  dc.city_name,
  fm.temperature,
  fm.humidity,
  fm.aqi,
  aq.level_name as air_quality
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dd ON fm.capture_date = dd.date_value
LEFT JOIN dim_air_quality_level aq ON fm.aqi_level_id = aq.aqi_level_id
ORDER BY fm.captured_at DESC
LIMIT 10;
```

**Statistiques par ville (30 jours)** :
```sql
SELECT 
  dc.city_name,
  COUNT(*) as nb_mesures,
  ROUND(AVG(fm.temperature), 1) as temp_moyenne,
  ROUND(AVG(fm.aqi), 0) as aqi_moyen,
  ROUND(AVG(fm.pm25), 1) as pm25_moyen
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dd ON fm.capture_date = dd.date_value
WHERE dd.date_value >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dc.city_name
ORDER BY dc.city_name;
```

**Anomalies critiques récentes** :
```sql
SELECT * FROM v_critical_anomalies
ORDER BY detected_at DESC
LIMIT 20;
```

**Statistiques ML par ville** :
```sql
SELECT * FROM get_city_stats('Paris', 30);
```

**Résumé anomalies (7 derniers jours)** :
```sql
SELECT * FROM get_anomaly_summary(7);
```

#### B. Scripts de diagnostic

Le dossier `scripts/temp/` contient des scripts de diagnostic (non versionnés Git) :

```bash
# Statut global de la BDD
python scripts/temp/check_bdd_status.py

# Vérification du schéma en étoile
python scripts/temp/verify_star_schema.py

# Statut du Data Lake
python scripts/temp/check_data_lake.py

# Audit complet fact_measures
python scripts/temp/audit_fact_measures.py
```

#### C. Quotas API

**OpenWeather** :
- Plan gratuit : 1000 appels/jour
- Utilisation : 240 appels/jour (10 villes × 24h)
- Taux : **24%** ✅

**AQICN** :
- Varie selon le plan
- Utilisation : 240 appels/jour

#### D. Maintenance régulière

**Hebdomadaire** :
```bash
# Valider la qualité sur 7 jours
python scripts/validate_data_quality.py --hours 168
```

**Mensuelle** :
```sql
-- Vérifier la couverture sur 30 jours
SELECT 
  dc.city_name,
  COUNT(*) as nb_mesures,
  MIN(fm.captured_at) as premiere_mesure,
  MAX(fm.captured_at) as derniere_mesure
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
WHERE fm.captured_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dc.city_name
ORDER BY nb_mesures DESC;
```

### Étape 9 : Analyse des données

#### A. Requêtes OLAP

**Agrégation par saison** :
```sql
SELECT 
  dd.season,
  ROUND(AVG(fm.temperature), 1) as temp_moyenne,
  ROUND(AVG(fm.aqi), 0) as aqi_moyen
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
WHERE dd.year = 2026
GROUP BY dd.season
ORDER BY dd.season;
```

**Top 10 jours les plus pollués** :
```sql
SELECT 
  dd.date_value,
  dc.city_name,
  fm.aqi,
  aq.level_name
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
JOIN dim_city dc ON fm.city_id = dc.city_id
LEFT JOIN dim_air_quality_level aq ON fm.aqi_level_id = aq.aqi_level_id
WHERE fm.aqi IS NOT NULL
ORDER BY fm.aqi DESC
LIMIT 10;
```

**Comparaison villes (moyennes annuelles)** :
```sql
SELECT 
  dc.city_name,
  ROUND(AVG(fm.temperature), 1) as temp_moy,
  ROUND(AVG(fm.humidity), 0) as humidity_moy,
  ROUND(AVG(fm.aqi), 0) as aqi_moy,
  ROUND(AVG(fm.pm25), 1) as pm25_moy
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dd ON fm.capture_date = dd.date_value
WHERE dd.year = 2026
GROUP BY dc.city_name
ORDER BY aqi_moy DESC;
```

#### B. Détection d'anomalies ML

**Mesures flaggées avec scores** :
```sql
SELECT 
  dc.city_name AS ville,
  fm.captured_at,
  fm.temperature,
  fm.aqi,
  fm.anomaly_score,
  a.anomaly_type,
  a.severity,
  a.field_name,
  a.actual_value
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
LEFT JOIN anomalies a ON fm.measure_id = a.measure_id
WHERE fm.is_anomaly = TRUE
  AND fm.captured_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY fm.anomaly_score DESC, fm.captured_at DESC
LIMIT 20;
```

**Anomalies par type et sévérité** :
```sql
SELECT 
  anomaly_type,
  severity,
  COUNT(*) as count
FROM anomalies
WHERE detected_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY anomaly_type, severity
ORDER BY count DESC;
```

---

## 📁 Structure du projet

```
MSPR 1/
├── .github/workflows/          # GitHub Actions
│   ├── etl-extract.yml
│   ├── etl-transform.yml
│   └── data-quality-validation.yml
├── data/
│   └── cities_reference.json   # 10 villes (id, name, lat, lon)
├── docs/                       # Documentation technique
│   ├── README.md                     # Index
│   ├── ARCHITECTURE.md               # Architecture détaillée
│   ├── ANOMALY_DETECTION.md          # Guide ML
│   ├── SECURITE.md                   # RGPD et sécurité
│   └── archive/                      # Anciens docs
├── logs/                       # Logs d'exécution
├── scripts/
│   ├── import_aqicn_historical.py    # Import CSV historique
│   ├── process_all_remaining.py      # Traitement batch
│   ├── validate_data_quality.py      # Validation 5 niveaux
│   ├── README.md                     # Guide des scripts
│   └── temp/                         # Scripts diagnostic (Git-excluded)
├── sql/
│   ├── star_schema.sql               # Schéma en étoile
│   ├── create_dim_date.sql           # Dimension temporelle
│   ├── anomaly_detection_schema.sql  # Schéma ML
│   ├── anomaly_functions.sql         # Fonctions analytiques
│   ├── queries_olap.sql              # Requêtes d'analyse
│   └── README.md                     # Guide SQL
├── src/
│   ├── services/
│   │   ├── weather_service.py            # API OpenWeather
│   │   ├── air_quality_service.py        # API AQICN
│   │   ├── data_lake_service.py          # Gestion Data Lake
│   │   ├── database_service.py           # Supabase + Star Schema
│   │   └── anomaly_detection_service.py  # ML Isolation Forest
│   ├── config.py                     # Configuration centralisée
│   ├── etl_extract_to_lake.py       # Pipeline 1 (APIs → Lake)
│   └── etl_transform_to_db.py       # Pipeline 2 (Lake → Warehouse)
├── .env                        # Configuration (NON versionné)
├── .gitignore
├── requirements.txt            # Dépendances Python
├── CHANGELOG.md                # Historique des versions
└── README.md                   # Ce fichier
```

---

## 🔐 Sécurité et RGPD

**Conformité RGPD** :
- Hébergement Supabase : **eu-central-1** (Francfort, Allemagne)
- Pas de données personnelles collectées
- Données publiques uniquement (météo + qualité air)
- Retention : 4 ans (dim_date 2024-2027)

**Gestion des secrets** :
- Clés API dans `.env` (jamais commitées)
- `.gitignore` configuré
- GitHub Secrets pour CI/CD
- Service Key Supabase avec RLS

📖 **Documentation complète** : [docs/SECURITE.md](docs/SECURITE.md)

---

## 📊 Modèle de données

### Star Schema (Data Warehouse)

**Table de faits** :
- `fact_measures` : Mesures environnementales horaires
  - Métriques météo : temperature, pressure, humidity, wind_speed, uv_index, visibility
  - Métriques air : aqi, pm25, pm10, no2, o3, so2, co
  - Timestamp : `captured_at` (TIMESTAMP exact)
  - Flags ML : `is_anomaly`, `anomaly_score`

**Tables de dimensions** :
- `dim_date` : ~1460 jours (2024-2027) avec attributs calendaires
- `dim_city` : 10 villes avec coordonnées GPS
- `dim_weather_condition` : ~40 conditions météo
- `dim_air_quality_level` : 6 niveaux (Good → Severe)

### ML Anomaly Detection

**3 niveaux de détection** :
1. **Règles métier** : Limites physiques (temp -50 à 60°C, AQI 0-500, etc.)
2. **Analyse statistique** : Z-score sur 30 jours (seuils 2σ, 2.5σ, 3σ, 4σ)
3. **ML Isolation Forest** : Détection multivariée (5% contamination)

**Tables** :
- `anomalies` : Stockage des anomalies détectées
- `ml_model_metadata` : Métadonnées des modèles

**Fonctions SQL** :
- `get_city_stats(city_name, days)` : Statistiques par ville
- `get_anomaly_summary(days)` : Résumé des anomalies

📖 **Guide complet** : [docs/ANOMALY_DETECTION.md](docs/ANOMALY_DETECTION.md)

---

## 🛠️ Dépannage

### Erreur : "Connection to Supabase failed"

```bash
# Vérifier les variables d'environnement
cat .env | grep SUPABASE

# Tester la connexion
python -c "
from src.services.database_service import DatabaseService
from src.config import Config
db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
print('✅ Connexion réussie')
"
```

### Erreur : "API rate limit exceeded"

- OpenWeather : 1000 appels/jour max
- Utilisation normale : 240 appels/jour
- Solution : Vérifier si plusieurs instances tournent

### Data Lake vide après extraction

```bash
# Vérifier les logs
cat logs/etl_extract_*.log

# Relancer l'extraction
python src/etl_extract_to_lake.py
```

### Anomalies non détectées

```bash
# Vérifier qu'il y a assez de données historiques
python -c "
from src.services.database_service import DatabaseService
from src.config import Config
db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
count = db.client.table('fact_measures').select('*', count='exact').execute()
print(f'Mesures : {count.count} (minimum 100 pour ML)')
"
```

---

## 📚 Documentation

- [docs/README.md](docs/README.md) - Index de la documentation
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture technique
- [docs/ANOMALY_DETECTION.md](docs/ANOMALY_DETECTION.md) - Guide ML
- [docs/SECURITE.md](docs/SECURITE.md) - Sécurité et RGPD
- [CHANGELOG.md](CHANGELOG.md) - Historique des versions
- [scripts/README.md](scripts/README.md) - Guide des scripts
- [sql/README.md](sql/README.md) - Guide SQL

---

## 🔗 Liens utiles

- **GitHub** : [Bastien-rab35/totalgreen-etl](https://github.com/Bastien-rab35/totalgreen-etl)
- **Supabase** : [uqntmecpgswkdchcfwxe.supabase.co](https://uqntmecpgswkdchcfwxe.supabase.co)
- **OpenWeather API** : [openweathermap.org](https://openweathermap.org)
- **AQICN API** : [aqicn.org](https://aqicn.org)

---

**Version** : 2.1.0 (Import CSV historique + Validation qualité)  
**Créé** : Janvier 2026  
**Conformité** : RGPD (hébergement EU)  
**Automatisation** : GitHub Actions (collecte horaire)
