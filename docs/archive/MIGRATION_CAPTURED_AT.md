# Migration vers Architecture Simplifiée : captured_at + dim_date

## 🎯 Objectif

Simplifier l'architecture du Data Warehouse en :
- Stockant le timestamp `captured_at` directement dans `fact_measures`
- Créant une dimension `dim_date` légère (sans heures)
- Supprimant la dépendance à `dim_time` et `time_id`

## ✅ Migrations Effectuées

### 1. Ajout de `captured_at` dans `fact_measures`

**Script** : `sql/migration_add_captured_at.sql`

**Actions** :
- ✅ Ajout colonne `captured_at TIMESTAMP WITH TIME ZONE`
- ✅ Remplissage depuis `dim_time.full_date` (jointure sur `time_id`)
- ✅ Contrainte NOT NULL ajoutée
- ✅ Index créés : `idx_fact_measures_captured_at`, `idx_fact_measures_city_captured`

**Résultat** : 5401 mesures migrées avec succès

### 2. Création de `dim_date`

**Script** : `sql/create_dim_date.sql`

**Structure** :
```sql
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,  -- Format YYYYMMDD (ex: 20260209)
    date_value DATE NOT NULL UNIQUE,
    
    -- Jour
    day_of_month, day_of_week, day_name, day_of_year,
    
    -- Semaine
    week_of_year, week_of_month,
    
    -- Mois
    month, month_name,
    
    -- Trimestre
    quarter, quarter_name,
    
    -- Année
    year,
    
    -- Indicateurs
    is_weekend, is_holiday, season
);
```

**Données** : 1461 jours (2024-01-01 → 2027-12-31)

### 3. Mise à jour du code ETL

**Fichiers modifiés** :
- ✅ `src/services/database_service.py`
  - `insert_into_star_schema()` : Supprimé lookup `time_id`, ajout direct `captured_at`
  - `get_historical_data_for_ml()` : `ORDER BY captured_at` au lieu de `time_id`

- ✅ `src/etl_transform_to_db.py`
  - Déjà utilisait `captured_at` directement (aucune modification nécessaire)

## 📊 Avantages de la Nouvelle Architecture

### Avant (avec time_id)
```python
# Complexe : chercher time_id pour chaque insertion
dt = datetime.fromisoformat(captured_at)
hour_truncated = dt.replace(minute=0, second=0, microsecond=0)
time_result = db.query('dim_time', {'full_date': hour_truncated})
time_id = time_result[0]['time_id']

data = {'time_id': time_id, ...}
```

### Après (avec captured_at)
```python
# Simple : timestamp direct
data = {'captured_at': captured_at, ...}
```

### Requêtes simplifiées

**Avant** :
```sql
SELECT fm.temperature, dt.date_only, dt.hour
FROM fact_measures fm
JOIN dim_time dt ON fm.time_id = dt.time_id;
```

**Après** :
```sql
-- Timestamp exact
SELECT temperature, captured_at FROM fact_measures;

-- Avec attributs dérivés
SELECT fm.temperature, fm.captured_at, dd.day_name, dd.season
FROM fact_measures fm
JOIN dim_date dd ON DATE(fm.captured_at) = dd.date_value;
```

## 🔄 Utilisation de dim_date

### Analyses temporelles

```sql
-- Moyenne par jour de la semaine
SELECT 
    dd.day_name,
    ROUND(AVG(fm.temperature), 1) as avg_temp
FROM fact_measures fm
JOIN dim_date dd ON DATE(fm.captured_at) = dd.date_value
GROUP BY dd.day_name, dd.day_of_week
ORDER BY dd.day_of_week;

-- Tendances par saison
SELECT 
    dd.season,
    ROUND(AVG(fm.aqi_index), 0) as avg_aqi
FROM fact_measures fm
JOIN dim_date dd ON DATE(fm.captured_at) = dd.date_value
GROUP BY dd.season;

-- Weekend vs semaine
SELECT 
    dd.is_weekend,
    COUNT(*) as nb_measures,
    ROUND(AVG(fm.temperature), 1) as avg_temp
FROM fact_measures fm
JOIN dim_date dd ON DATE(fm.captured_at) = dd.date_value
GROUP BY dd.is_weekend;
```

## 🗑️ Nettoyage (Optionnel)

Si tu veux supprimer `dim_time` et `time_id` :

```sql
-- 1. Supprimer la colonne time_id de fact_measures
ALTER TABLE fact_measures DROP COLUMN IF EXISTS time_id;

-- 2. Supprimer dim_time
DROP TABLE IF EXISTS dim_time CASCADE;
```

⚠️ **Attention** : Assure-toi que toutes les requêtes et dashboards n'utilisent plus `time_id` avant !

## 📝 Prochaines Étapes

1. ✅ Tester les insertions avec le nouveau code
2. ✅ Vérifier les requêtes d'analyse
3. ⏳ Mettre à jour les dashboards (si existants)
4. ⏳ Nettoyer `dim_time` si confirmé inutile

## 🎓 Documentation Mise à Jour

- [x] `sql/migration_add_captured_at.sql` - Script de migration
- [x] `sql/create_dim_date.sql` - Création de la nouvelle dimension
- [x] `docs/MIGRATION_CAPTURED_AT.md` - Ce document
- [ ] `README.md` - Mettre à jour l'architecture (remplacer dim_time par dim_date)
- [ ] `docs/ARCHITECTURE.md` - Documenter la nouvelle structure

## 🔗 Références

- **Kimball Methodology** : Recommande timestamps dans fact tables
- **PostgreSQL Best Practices** : Index sur TIMESTAMP pour séries temporelles
- **Star Schema Simplified** : Dimensions légères = meilleure performance
