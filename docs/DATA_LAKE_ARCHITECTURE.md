# 📊 ARCHITECTURE DATA LAKE - TotalGreen

## Vue d'ensemble de l'architecture ELT

Le projet utilise une architecture **ELT (Extract-Load-Transform)** moderne avec un **Data Lake JSONB** :

```
┌─────────────────────────────────────────────────────────────┐
│                   SOURCES EXTERNES                          │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │  OpenWeather API │          │    AQICN API     │        │
│  │   (Météo JSON)   │          │ (Air Quality)    │        │
│  └──────────────────┘          └──────────────────┘        │
└──────────────┬─────────────────────────┬───────────────────┘
               │                         │
               │ EXTRACT                 │
               ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│            ÉTAPE 1: LOAD → DATA LAKE (JSONB)                │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Table: raw_data_lake                       │    │
│  │  - Stockage JSONB des données brutes               │    │
│  │  - Pas de transformation                           │    │
│  │  - Traçabilité complète (timestamp, source)        │    │
│  │  - Indexation GIN pour requêtes JSON               │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           │ TRANSFORM
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         ÉTAPE 2: TRANSFORM → TABLES STRUCTURÉES             │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Table: measures                            │    │
│  │  - Données normalisées et typées                   │    │
│  │  - Colonnes structurées (temp, humidity, aqi...)   │    │
│  │  - Références vers raw_data_lake (traçabilité)     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Avantages de cette architecture

### ✅ Conformité cahier des charges
- **Data Lake** : Stockage intermédiaire des données brutes
- **Traçabilité** : Lien entre données brutes et transformées
- **Auditabilité** : Possibilité de retracer toute transformation

### ✅ Flexibilité
- Les données JSON brutes sont conservées
- Possibilité de retraiter les données avec d'autres algorithmes
- Ajout de nouvelles transformations sans nouvelle collecte

### ✅ Performance
- Index GIN sur le JSONB pour requêtes rapides
- Requêtes SQL possibles sur les données JSON
- Séparation lecture/écriture optimisée

### ✅ Sécurité et RGPD
- Données stockées en UE (Supabase)
- Conservation de l'historique complet
- Possibilité de purge des anciennes données

## Tables créées

### 1. `raw_data_lake` (Data Lake)

```sql
CREATE TABLE raw_data_lake (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    city_name VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,        -- 'openweather' ou 'aqicn'
    raw_data JSONB NOT NULL,            -- Données JSON brutes
    collected_at TIMESTAMP WITH TIME ZONE,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE
);
```

**Exemple de données stockées** :
```json
{
  "source": "openweather",
  "city_name": "Paris",
  "raw_data": {
    "coord": {"lon": 2.3522, "lat": 48.8566},
    "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
    "main": {
      "temp": 15.5,
      "feels_like": 14.2,
      "pressure": 1013,
      "humidity": 72
    },
    "wind": {"speed": 3.5, "deg": 230}
  }
}
```

### 2. `measures` (Données transformées)

```sql
CREATE TABLE measures (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    raw_weather_id BIGINT REFERENCES raw_data_lake(id),  -- Traçabilité
    raw_aqi_id BIGINT REFERENCES raw_data_lake(id),      -- Traçabilité
    captured_at TIMESTAMP WITH TIME ZONE,
    
    -- Données météo transformées
    temp DECIMAL(5,2),
    humidity INTEGER,
    wind_speed DECIMAL(5,2),
    ...
    
    -- Données AQI transformées
    aqi_index INTEGER,
    pm25 DECIMAL(7,2),
    ...
);
```

## Flux de données (Pipeline ETL)

```python
# 1. EXTRACT
weather_data = weather_service.fetch_weather_data("Paris")
# Retourne: {'raw': {...}, 'parsed': {...}}

# 2. LOAD dans Data Lake (JSONB)
raw_id = data_lake_service.store_raw_data(
    city_id=1,
    city_name="Paris",
    source="openweather",
    raw_data=weather_data['raw']  # JSON complet
)

# 3. TRANSFORM et LOAD dans tables structurées
db_service.insert_measure(
    city_id=1,
    weather_data=weather_data['parsed'],  # Données transformées
    raw_weather_id=raw_id  # Lien vers data lake
)

# 4. Marquer comme traité
data_lake_service.mark_as_processed(raw_id)
```

## Requêtes possibles sur le Data Lake

### Recherche dans le JSONB

```sql
-- Températures > 30°C
SELECT 
    city_name,
    raw_data->'main'->>'temp' AS temperature,
    collected_at
FROM raw_data_lake
WHERE source = 'openweather'
  AND (raw_data->'main'->>'temp')::float > 30;
```

### Traçabilité complète

```sql
-- Voir la donnée brute qui a généré une mesure
SELECT 
    m.temp AS transformed_temp,
    rdl.raw_data->'main'->>'temp' AS raw_temp,
    m.captured_at
FROM measures m
JOIN raw_data_lake rdl ON m.raw_weather_id = rdl.id
WHERE m.city_id = 1
LIMIT 10;
```

### Export pour analyse

```sql
-- Export JSON complet
SELECT raw_data 
FROM raw_data_lake
WHERE city_name = 'Paris'
  AND collected_at >= NOW() - INTERVAL '7 days';
```

## Maintenance du Data Lake

### Retraitement des données

```python
# Récupérer les données non traitées
unprocessed = data_lake_service.get_unprocessed_data()

for record in unprocessed:
    # Appliquer une nouvelle transformation
    transformed = my_new_transform(record['raw_data'])
    # Sauvegarder
    db_service.insert_measure(...)
    # Marquer comme traité
    data_lake_service.mark_as_processed(record['id'])
```

### Purge des anciennes données

```sql
-- Supprimer les données > 90 jours (déjà traitées)
DELETE FROM raw_data_lake 
WHERE collected_at < NOW() - INTERVAL '90 days' 
  AND processed = TRUE;
```

## Utilisation des services

### DataLakeService

```python
from services import DataLakeService

# Initialisation
lake = DataLakeService(supabase_url, supabase_key)

# Stocker des données brutes
lake_id = lake.store_raw_data(
    city_id=1,
    city_name="Paris",
    source="openweather",
    raw_data={"temp": 15.5, ...}
)

# Marquer comme traité
lake.mark_as_processed(lake_id)

# Récupérer les données non traitées
unprocessed = lake.get_unprocessed_data(limit=100)

# Export vers fichier JSON
lake.export_to_json_file("Paris", output_dir="data/lake")
```

## Conformité et Avantages

### ✅ Répond au cahier des charges
- **Data Lake** : Couche intermédiaire de stockage
- **JSONB** : Format moderne, flexible et performant
- **Traçabilité** : Lien entre raw et transformed data

### ✅ Bonnes pratiques data engineering
- Architecture ELT moderne
- Séparation des responsabilités
- Idempotence (retraitement possible)

### ✅ Évolutivité
- Ajout de nouvelles sources facile
- Changement de transformation sans perte de données
- Support de l'analyse ad-hoc sur JSON

---

**Architecture validée** pour les phases 2 et 3 du projet TotalGreen 🚀
