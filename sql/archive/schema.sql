-- ============================================
-- Schéma de base de données TotalGreen
-- Projet de collecte environnementale
-- Localisation: UE (eu-central-1 ou eu-west-3)
-- ============================================

-- ============================================
-- TABLES DE RÉFÉRENCE
-- ============================================

-- Table des Villes (Référentiel)
CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    timezone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches par nom de ville
CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name);

-- ============================================
-- DATA LAKE - Stockage des données brutes (JSONB)
-- ============================================

-- Table de stockage des données brutes JSON
CREATE TABLE IF NOT EXISTS raw_data_lake (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id) ON DELETE CASCADE,
    city_name VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'openweather' ou 'aqicn'
    raw_data JSONB NOT NULL, -- Données JSON brutes de l'API
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_raw_data_lake_city_id ON raw_data_lake(city_id);
CREATE INDEX IF NOT EXISTS idx_raw_data_lake_source ON raw_data_lake(source);
CREATE INDEX IF NOT EXISTS idx_raw_data_lake_collected_at ON raw_data_lake(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_lake_processed ON raw_data_lake(processed);
CREATE INDEX IF NOT EXISTS idx_raw_data_lake_raw_data ON raw_data_lake USING GIN (raw_data);

COMMENT ON TABLE raw_data_lake IS 'Data Lake - Stockage des données brutes JSON avant transformation';

-- ============================================
-- TABLES TRANSFORMÉES
-- ============================================

-- Table des Mesures (Historisation horaire)
CREATE TABLE IF NOT EXISTS measures (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id) ON DELETE CASCADE,
    raw_weather_id BIGINT REFERENCES raw_data_lake(id),
    raw_aqi_id BIGINT REFERENCES raw_data_lake(id),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Variables OpenWeather (Current)
    temp DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    pressure INTEGER,
    humidity INTEGER,
    dew_point DECIMAL(5,2),
    clouds INTEGER,
    uvi DECIMAL(4,2),
    visibility INTEGER,
    wind_speed DECIMAL(5,2),
    wind_deg INTEGER,
    wind_gust DECIMAL(5,2),
    rain_1h DECIMAL(5,2) DEFAULT 0,
    snow_1h DECIMAL(5,2) DEFAULT 0,
    weather_id INTEGER,
    weather_main VARCHAR(50),
    weather_description VARCHAR(100),
    
    -- Variables Air Quality (AQICN)
    aqi_index INTEGER,
    pm25 DECIMAL(7,2),
    pm10 DECIMAL(7,2),
    no2 DECIMAL(7,2),
    o3 DECIMAL(7,2),
    so2 DECIMAL(7,2),
    co DECIMAL(7,2),
    station_attribution TEXT,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches temporelles
CREATE INDEX IF NOT EXISTS idx_measures_captured_at ON measures(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_measures_city_id ON measures(city_id);
CREATE INDEX IF NOT EXISTS idx_measures_city_date ON measures(city_id, captured_at DESC);

-- Table de monitoring (Health Check)
CREATE TABLE IF NOT EXISTS etl_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'warning'
    source VARCHAR(50), -- 'openweather', 'aqicn', 'both'
    city_id INTEGER REFERENCES cities(id),
    records_inserted INTEGER DEFAULT 0,
    error_message TEXT,
    execution_duration_seconds DECIMAL(10,2)
);

-- Index pour le monitoring
CREATE INDEX IF NOT EXISTS idx_etl_logs_status ON etl_logs(status);
CREATE INDEX IF NOT EXISTS idx_etl_logs_execution_time ON etl_logs(execution_time DESC);

-- Vue pour faciliter l'analyse des données complètes
CREATE VIEW v_measures_complete AS
SELECT 
    m.id,
    c.name AS city_name,
    c.latitude,
    c.longitude,
    m.captured_at,
    m.temp,
    m.feels_like,
    m.pressure,
    m.humidity,
    m.wind_speed,
    m.wind_deg,
    m.aqi_index,
    m.pm25,
    m.pm10,
    m.weather_main,
    m.weather_description
FROM measures m
JOIN cities c ON m.city_id = c.id;

-- Politiques de sécurité RLS (Row Level Security)
-- À activer dans Supabase selon les besoins d'authentification
-- ALTER TABLE cities ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE measures ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE etl_logs ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE cities IS 'Référentiel des villes métropolitaines françaises surveillées';
COMMENT ON TABLE measures IS 'Historisation horaire des mesures météorologiques et de qualité de l\'air (données transformées)';
COMMENT ON TABLE etl_logs IS 'Journal de surveillance des exécutions ETL pour alertes';

-- ============================================
-- ARCHITECTURE DATA LAKE
-- ============================================
-- 1. raw_data_lake : Stockage brut des données JSON (Extract + Load)
-- 2. measures : Données transformées et structurées (Transform)
-- 3. Traçabilité via raw_weather_id et raw_aqi_id
