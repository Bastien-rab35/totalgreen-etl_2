# Schéma d'Architecture Principale

Ce schéma montre l'architecture complète du système avec les flux de données entre les différents composants.

```mermaid
graph TB
    subgraph "Sources de Données Externes"
        API1[OpenWeather API<br/>Données Météo]
        API2[AQICN API<br/>Qualité de l'Air]
    end

    subgraph "Couche ETL - Extract"
        ETL_E[etl_extract_to_lake.py<br/>Collecte des données brutes]
        WS[WeatherService]
        AQS[AirQualityService]
    end

    subgraph "Data Lake - Stockage Brut"
        DL[(raw_data_lake<br/>Supabase Table)]
        DLS[DataLakeService]
    end

    subgraph "Couche ETL - Transform & Load"
        ETL_T[etl_transform_to_db.py<br/>Transformation & Chargement]
        DBS[DatabaseService]
    end

    subgraph "Data Warehouse - Schéma en Étoile"
        DW[(Supabase PostgreSQL)]
        
        subgraph "Tables de Dimensions"
            D1[dim_city<br/>10 villes]
            D2[dim_weather_condition<br/>36 conditions]
            D3[dim_air_quality_level<br/>6 niveaux]
            D4[dim_date<br/>1461 jours]
        end
        
        subgraph "Table de Faits"
            F1[fact_measures<br/>14,904 mesures]
        end
    end

    subgraph "Analyse & Détection"
        ADS[AnomalyDetectionService]
        FUNC[anomaly_functions.sql<br/>Fonctions SQL]
        SCHEMA[anomaly_detection_schema.sql]
    end

    subgraph "Scripts de Vérification"
        S1[check_database_complete.py]
        S2[verify_star_schema.py]
        S3[check_lyon_aqi.py]
        S4[diagnostic_lyon_aqi.py]
    end

    subgraph "Configuration"
        CONF[config.py<br/>Variables d'environnement]
        REF[cities_reference.json<br/>10 villes françaises]
    end

    %% Flux de données
    API1 --> WS
    API2 --> AQS
    WS --> ETL_E
    AQS --> ETL_E
    ETL_E --> DLS
    DLS --> DL
    
    DL --> ETL_T
    ETL_T --> DBS
    DBS --> DW
    
    DW --> D1
    DW --> D2
    DW --> D3
    DW --> D4
    DW --> F1
    
    F1 -.Jointures.-> D1
    F1 -.Jointures.-> D2
    F1 -.Jointures.-> D3
    F1 -.Jointures.-> D4
    
    CONF -.Configuration.-> ETL_E
    CONF -.Configuration.-> ETL_T
    REF -.Référence.-> D1
    
    DW --> ADS
    FUNC --> DW
    SCHEMA --> DW
    
    DW --> S1
    DW --> S2
    DW --> S3
    DW --> S4

    %% Style
    classDef apiClass fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef etlClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storageClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef serviceClass fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef dimClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef factClass fill:#ffccbc,stroke:#bf360c,stroke-width:3px
    classDef scriptClass fill:#e0e0e0,stroke:#424242,stroke-width:1px
    
    class API1,API2 apiClass
    class ETL_E,ETL_T etlClass
    class DL,DW storageClass
    class WS,AQS,DLS,DBS,ADS serviceClass
    class D1,D2,D3,D4 dimClass
    class F1 factClass
    class S1,S2,S3,S4,CONF,REF,FUNC,SCHEMA scriptClass
```

## Légende

| Couleur | Composant |
|---------|-----------|
| 🔵 Bleu clair | APIs Externes |
| 🟠 Orange | Pipeline ETL |
| 🟣 Violet | Stockage (Data Lake, Data Warehouse) |
| 🟢 Vert | Services |
| 🟡 Jaune | Tables de Dimensions |
| 🔴 Rouge/Orange | Table de Faits |
| ⚫ Gris | Scripts & Configuration |

## Description des Composants

### Sources de Données
- **OpenWeather API** : Fournit les données météorologiques
- **AQICN API** : Fournit les données de qualité de l'air

### Services
- **WeatherService** : Gestion des appels à OpenWeather API
- **AirQualityService** : Gestion des appels à AQICN API
- **DataLakeService** : Gestion du stockage dans le Data Lake
- **DatabaseService** : Gestion de la connexion Supabase
- **AnomalyDetectionService** : Détection des valeurs anormales

### Pipeline ETL
- **etl_extract_to_lake.py** : Extraction et stockage brut
- **etl_transform_to_db.py** : Transformation et chargement

### Stockage
- **raw_data_lake** : Stockage brut des réponses API (20,706 enregistrements)
- **Data Warehouse** : Schéma en étoile optimisé pour l'analyse

### Tables de Dimensions
- **dim_city** : Référentiel des villes
- **dim_weather_condition** : Types de conditions météorologiques
- **dim_air_quality_level** : Niveaux de qualité de l'air
- **dim_date** : Dimension temporelle (calendrier)

### Table de Faits
- **fact_measures** : Mesures environnementales (14,904 enregistrements)
