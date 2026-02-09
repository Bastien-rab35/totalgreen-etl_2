# TotalGreen - Data Warehouse Environnemental ⭐

**Pipeline ETL automatisé** pour la collecte et l'analyse de données environnementales sur les 10 plus grandes villes métropolitaines françaises.

## 🎯 Vue d'ensemble

Pipeline de données **production-ready** avec :
- **Collecte automatisée** : APIs OpenWeather + AQICN (toutes les heures via GitHub Actions)
- **Data Lake JSONB** : Stockage brut des données avec versioning
- **Data Warehouse** : Modèle en **étoile** optimisé pour l'analyse
- **Conformité RGPD** : Hébergement EU (Francfort) avec sécurité renforcée

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              PIPELINE 1 : EXTRACTION (toutes les heures)     │
│  APIs (OpenWeather + AQICN) → Data Lake (JSONB) → Lake      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         PIPELINE 2 : TRANSFORMATION (toutes les heures)      │
│  Data Lake → Transform → Data Warehouse (Star Schema) ⭐     │
└─────────────────────────────────────────────────────────────┘
```

### Structure du projet

```
MSPR 1/
├── data/
│   └── cities_reference.json     # Référentiel des 10 villes
├── docs/                         # 📚 Documentation
│   ├── README.md                 # Index de la documentation
│   ├── ARCHITECTURE.md           # Architecture technique détaillée
│   ├── SECURITE.md              # RGPD et sécurité
│   └── archive/                 # Anciens documents techniques
├── logs/                         # Logs d'exécution
├── sql/
│   ├── star_schema.sql          # ⭐ Schéma en étoile (Data Warehouse)
│   └── archive/                 # Anciens scripts SQL
├── scripts/
│   ├── check_bdd_status.py      # Vérification BDD
│   ├── check_data_lake.py       # Vérification Data Lake
│   └── archive/                 # Scripts de migration
├── src/
│   ├── services/
│   │   ├── weather_service.py        # API OpenWeather
│   │   ├── air_quality_service.py    # API AQICN
│   │   ├── data_lake_service.py      # Gestion Data Lake
│   │   └── database_service.py       # Supabase + Star Schema
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

Dans l'éditeur SQL Supabase, exécutez :
```sql
-- Créer le schéma en étoile (⭐ Data Warehouse)
\i sql/star_schema.sql
```

Cela crée :
- **4 tables de dimensions** : dim_time, dim_city, dim_weather_condition, dim_air_quality_level
- **1 table de faits** : fact_measures
- **~26 000 périodes** dans dim_time (couvre 3 ans)

## 📦 Utilisation

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

Le Data Warehouse utilise un **schéma en étoile** optimisé pour l'analyse :

### Table de faits
- **`fact_measures`** : Mesures environnementales horaires
  - Métriques météo : température, pression, humidité, vent, UV, visibilité
  - Métriques qualité de l'air : AQI, PM2.5, PM10, NO2, O3, SO2, CO
  - Clés étrangères : `time_id`, `city_id`, `weather_condition_id`, `aqi_level_id`

### Tables de dimensions
- **`dim_time`** : Dimension temporelle
  - ~26 000 périodes (date, heure, jour semaine, mois, trimestre, année, saison)
  - Pré-remplie pour 3 ans
  
- **`dim_city`** : Dimension géographique
  - 10 villes françaises avec coordonnées GPS
  
- **`dim_weather_condition`** : Conditions météo
  - 40+ conditions (Clear, Clouds, Rain, Snow, etc.)
  
- **`dim_air_quality_level`** : Niveaux de qualité de l'air
  - 6 niveaux (Good, Fair, Moderate, Poor, Very Poor, Severe)

### Avantages
✅ Requêtes optimisées pour l'analyse
✅ Agrégations temporelles rapides
✅ Jointures simplifiées
✅ Évolutivité garantie

## 💾 Data Lake

### Table `lake`
- Stockage **JSONB** des données brutes API
- Colonnes : `city_name`, `source`, `data_type`, `raw_data`, `captured_at`, `processed`
- Permet : audit, retraitement, versioning des données

### Workflow
1. **Extraction** : API → Data Lake (`processed=false`)
2. **Transformation** : Data Lake → Validation → Star Schema
3. **Marquage** : `processed=true` après insertion réussie

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

## 📊 Monitoring

### Vérifications système

```bash
# Statut de la base de données
python scripts/check_bdd_status.py

# Statut du data lake
python scripts/check_data_lake.py
```

### Requêtes utiles

```sql
-- Dernières mesures
SELECT 
  dt.date_full,
  dt.hour_24,
  dc.city_name,
  fm.temperature,
  fm.aqi,
  aq.level_name as air_quality
FROM fact_measures fm
JOIN dim_time dt ON fm.time_id = dt.time_id
JOIN dim_city dc ON fm.city_id = dc.city_id
LEFT JOIN dim_air_quality_level aq ON fm.aqi_level_id = aq.aqi_level_id
ORDER BY dt.date_full DESC, dt.hour_24 DESC
LIMIT 10;

-- Statistiques par ville
SELECT 
  dc.city_name,
  COUNT(*) as nb_mesures,
  ROUND(AVG(fm.temperature), 1) as temp_moyenne,
  ROUND(AVG(fm.aqi), 0) as aqi_moyen
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
GROUP BY dc.city_name
ORDER BY dc.city_name;
```

## 📈 Performance & Quotas

### Quotas API (plan gratuit)
- **OpenWeather** : 1000 appels/jour
  - Utilisation : 240 appels/jour (10 villes × 24h)
  - Taux : **24%** ✅
  
- **AQICN** : Varie selon le plan
  - Utilisation : 240 appels/jour

### Métriques du Data Warehouse
- **dim_time** : ~26 000 périodes (3 ans)
- **dim_city** : 10 villes
- **dim_weather_condition** : 40+ conditions
- **dim_air_quality_level** : 6 niveaux
- **fact_measures** : Croissance ~240 mesures/jour

## 📚 Documentation

- **[docs/README.md](docs/README.md)** - Index de la documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture technique détaillée
- **[docs/SECURITE.md](docs/SECURITE.md)** - Sécurité et RGPD
- **[docs/archive/](docs/archive/)** - Anciens documents techniques

## 🎓 Livrables du projet

### ✅ Phase 1 : Architecture & Data Lake
- Data Lake JSONB avec versioning
- Pipeline Extract → Lake automatisé

### ✅ Phase 2 : Data Warehouse ⭐
- Modèle en étoile (5 tables)
- Pipeline Transform → Warehouse
- Migration ~500 mesures historiques

### ✅ Phase 3 : Automatisation & Production
- GitHub Actions (2 workflows)
- Monitoring et logs
- Conformité RGPD

### 🚧 Phase 4 : Analyse (en cours)
- Dashboards Metabase (+5 points)
- ML/Anomaly Detection (+5 points)

## 🛠️ Dépannage

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
**🏷️ Version** : 2.0.0 (Star Schema)  
**✅ Conformité** : RGPD (hébergement EU)  
**⚡ Automatisation** : GitHub Actions  
**📊 Score** : 41/45 points (91%)
