# TotalGreen - Collecte de Données Environnementales

Projet de surveillance environnementale pour les 10 plus grandes villes métropolitaines françaises.

##  Vue d'ensemble

Ce projet collecte automatiquement des données météorologiques (OpenWeather) et de qualité de l'air (AQICN) pour 10 villes françaises, avec stockage sécurisé dans Supabase (PostgreSQL) en conformité RGPD.

## Architecture

```
MSPR 1/
├── data/                      # Données de référence
│   └── cities_reference.json  # Liste des 10 villes avec coordonnées GPS
├── logs/                      # Logs d'exécution
├── sql/                       # Scripts SQL
│   ├── schema.sql            # Schéma complet de la base de données
│   └── insert_cities.sql     # Insertion du référentiel des villes
├── src/                       # Code source
│   ├── services/             # Services modulaires
│   │   ├── weather_service.py      # API OpenWeather
│   │   ├── air_quality_service.py  # API AQICN
│   │   └── database_service.py     # Supabase
│   ├── config.py             # Configuration centralisée
│   ├── etl_pipeline.py       # Pipeline ETL principal
│   ├── scheduler.py          # Automatisation horaire
│   └── test_connections.py   # Tests de validation
├── .env                       # Variables d'environnement (SECRET)
├── .env.example              # Exemple de configuration
├── requirements.txt          # Dépendances Python
└── README.md                 # Cette documentation
```

## Installation

### 1. Prérequis

- Python 3.8+
- Compte Supabase (région UE: eu-central-1 ou eu-west-3)
- Clés API OpenWeather et AQICN

### 2. Installation des dépendances

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

Copiez `.env.example` vers `.env` et remplissez les valeurs :

```bash
cp .env.example .env
```

Éditez `.env` avec vos clés API :

```
OPENWEATHER_API_KEY=votre_clé_openweather
AQICN_API_KEY=votre_clé_aqicn
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_clé_service
AWS_REGION=eu-central-1
```

### 4. Configuration de la base de données

Dans Supabase, exécutez les scripts SQL dans l'ordre :

```sql
-- 1. Créer le schéma
\i sql/schema.sql

-- 2. Insérer les villes
\i sql/insert_cities.sql
```

## Tests

Avant la première exécution, testez les connexions :

```bash
cd src
python test_connections.py
```

Vérifications effectuées :
- ✓ Validation de la configuration
- ✓ Connexion à l'API OpenWeather
- ✓ Connexion à l'API AQICN
- ✓ Connexion à Supabase
- ✓ Estimation des quotas (240/1000 appels/jour)

## Utilisation

### Exécution manuelle (ponctuelle)

```bash
cd src
python etl_pipeline.py
```

### Exécution automatisée (horaire)

```bash
cd src
python scheduler.py
```

Le scheduler :
- Exécute le pipeline immédiatement au démarrage
- Répète toutes les 60 minutes (configurable dans `.env`)
- Enregistre tous les événements dans `logs/`

### Arrêt du scheduler

```bash
Ctrl+C
```

## 📊 Structure de la base de données

### Table `cities`
- Référentiel des 10 villes
- Coordonnées GPS (latitude, longitude)
- Timezone

### Table `measures`
- Mesures horaires
- **Météo** : température, pression, humidité, vent, UV, etc.
- **Qualité de l'air** : AQI, PM2.5, PM10, NO2, O3, SO2, CO

### Table `etl_logs`
- Monitoring des exécutions
- Statut (success/error/warning)
- Durée d'exécution
- Nombre d'enregistrements insérés

### Vue `v_measures_complete`
- Vue consolidée pour l'analyse
- Jointure cities + measures

## 🔒 Sécurité et RGPD

### Localisation des données
- Serveur Supabase en UE : **eu-central-1** (Francfort) ou **eu-west-3** (Paris)
- Conformité RGPD garantie

### Gestion des secrets
- Clés API stockées dans `.env` (jamais dans Git)
- `.gitignore` configuré pour exclure les fichiers sensibles

### Contrôle d'accès
- Authentification par clé de service Supabase
- RLS (Row Level Security) disponible dans le schéma SQL

### Surveillance
- Logs d'exécution dans `etl_logs`
- Alertes en cas d'échec

## 📈 Quotas API

### OpenWeather
- **Limite** : 1000 appels/jour (plan gratuit)
- **Utilisation** : 240 appels/jour (10 villes × 24h)
- **Taux** : 24%

### AQICN
- **Limite** : Varie selon le plan
- **Utilisation** : 240 appels/jour

## 🛠️ Maintenance

### Consulter les logs

```bash
# Logs ETL
tail -f logs/etl.log

# Logs du scheduler
tail -f logs/scheduler.log
```

### Vérifier les dernières mesures

```sql
SELECT * FROM v_measures_complete 
ORDER BY captured_at DESC 
LIMIT 10;
```

### Vérifier le statut des jobs

```sql
SELECT * FROM etl_logs 
ORDER BY execution_time DESC 
LIMIT 10;
```

## Livrables du projet

### Phase 1 : Initialisation & Audit
- Rapport d'audit de données
- Matrice de correspondance API
- Validation des quotas (240/1000)

### Phase 2 : Modélisation & Ingestion
- Schéma SQL (DDL)
- Pipeline ETL Python fonctionnel

### Phase 3 : Automatisation & Sécurité
- Système de collecte horaire automatisé
- Rapport de conformité RGPD
- Logs de monitoring

### Phase 4 : Restitution
- Dashboards de visualisation (à venir)
- Export pour analyse R/Excel (à venir)

## Dépannage

### Erreur de connexion Supabase
- Vérifiez `SUPABASE_URL` et `SUPABASE_KEY` dans `.env`
- Vérifiez que les tables sont créées

### Erreur API OpenWeather/AQICN
- Vérifiez vos clés API
- Vérifiez les quotas restants

### Aucune ville dans le référentiel
- Exécutez `sql/insert_cities.sql` dans Supabase

## Support

Pour toute question, consultez la documentation du projet ou contactez l'équipe TotalGreen.

---

**Date de création** : Janvier 2026  
**Version** : 1.0.0  
**Conformité** : RGPD (données hébergées en UE)
