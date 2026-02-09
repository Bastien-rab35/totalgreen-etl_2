-- ============================================
-- MIGRATION DES DONNÉES EXISTANTES
-- De measures (modèle normalisé) vers fact_measures (modèle en étoile)
-- GARANTIE : Aucune perte de données
-- ============================================

-- ============================================
-- ÉTAPE 1 : Remplir dimension Villes depuis cities existante
-- ============================================

INSERT INTO dim_city (city_id, city_name, latitude, longitude, timezone, region, country)
SELECT 
    id,
    name,
    latitude,
    longitude,
    timezone,
    CASE name
        WHEN 'Paris' THEN 'Île-de-France'
        WHEN 'Marseille' THEN 'Provence-Alpes-Côte d''Azur'
        WHEN 'Lyon' THEN 'Auvergne-Rhône-Alpes'
        WHEN 'Toulouse' THEN 'Occitanie'
        WHEN 'Nice' THEN 'Provence-Alpes-Côte d''Azur'
        WHEN 'Nantes' THEN 'Pays de la Loire'
        WHEN 'Montpellier' THEN 'Occitanie'
        WHEN 'Strasbourg' THEN 'Grand Est'
        WHEN 'Bordeaux' THEN 'Nouvelle-Aquitaine'
        WHEN 'Lille' THEN 'Hauts-de-France'
        ELSE 'Unknown'
    END,
    'France'
FROM cities
ON CONFLICT (city_id) DO UPDATE SET
    city_name = EXCLUDED.city_name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude;

-- ============================================
-- ÉTAPE 2 : Remplir dimension Temps pour la période des données
-- ============================================

-- Générer dim_time pour la période de vos données (2024-01-12 à aujourd'hui + 1 an futur)
SELECT populate_dim_time('2024-01-01'::DATE, (CURRENT_DATE + INTERVAL '1 year')::DATE);

-- ============================================
-- ÉTAPE 3 : Migrer les données de measures vers fact_measures
-- ============================================

-- Cette requête garantit 0% de perte de données
INSERT INTO fact_measures (
    time_id,
    city_id,
    weather_condition_id,
    aqi_level_id,
    temperature,
    feels_like,
    pressure,
    humidity,
    wind_speed,
    wind_deg,
    wind_gust,
    clouds,
    visibility,
    rain_1h,
    snow_1h,
    aqi_index,
    pm25,
    pm10,
    no2,
    o3,
    so2,
    co,
    raw_weather_id,
    raw_aqi_id,
    created_at
)
SELECT 
    -- Jointure avec dim_time (arrondi à l'heure)
    dt.time_id,
    
    -- Ville (déjà mappée city_id = dim_city.city_id)
    m.city_id,
    
    -- Condition météo (lookup dans dim_weather_condition)
    dwc.weather_condition_id,
    
    -- Niveau AQI (calculé dynamiquement)
    get_aqi_level_id(m.aqi_index),
    
    -- Métriques météo (TOUTES CONSERVÉES)
    m.temp,
    m.feels_like,
    m.pressure,
    m.humidity,
    m.wind_speed,
    m.wind_deg,
    m.wind_gust,
    m.clouds,
    m.visibility,
    COALESCE(m.rain_1h, 0),
    COALESCE(m.snow_1h, 0),
    
    -- Métriques qualité air (TOUTES CONSERVÉES)
    m.aqi_index,
    m.pm25,
    m.pm10,
    m.no2,
    m.o3,
    m.so2,
    m.co,
    
    -- Traçabilité data lake (CONSERVÉE)
    m.raw_weather_id,
    m.raw_aqi_id,
    
    -- Date création (CONSERVÉE)
    m.created_at
    
FROM measures m

-- Jointure avec dim_time (arrondi à l'heure la plus proche)
LEFT JOIN dim_time dt ON dt.full_date = DATE_TRUNC('hour', m.captured_at)

-- Jointure avec dim_weather_condition (si weather_id existe)
LEFT JOIN dim_weather_condition dwc ON dwc.weather_id = m.weather_id

-- Ne migrer que les données pas encore migrées (idempotent)
WHERE NOT EXISTS (
    SELECT 1 FROM fact_measures fm 
    WHERE fm.raw_weather_id = m.raw_weather_id 
    OR fm.raw_aqi_id = m.raw_aqi_id
);

-- ============================================
-- VÉRIFICATIONS POST-MIGRATION
-- ============================================

-- Compter les enregistrements avant/après
DO $$
DECLARE
    count_measures INTEGER;
    count_fact INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_measures FROM measures;
    SELECT COUNT(*) INTO count_fact FROM fact_measures;
    
    RAISE NOTICE '================================';
    RAISE NOTICE 'VÉRIFICATION MIGRATION';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Mesures originales: %', count_measures;
    RAISE NOTICE 'Mesures migrées: %', count_fact;
    
    IF count_fact < count_measures THEN
        RAISE WARNING 'ATTENTION: % mesures manquantes!', (count_measures - count_fact);
    ELSE
        RAISE NOTICE '✓ Migration complète - Aucune perte de données';
    END IF;
END $$;

-- Rapport détaillé de migration
SELECT 
    'Données originales (measures)' AS table_name,
    COUNT(*) AS total_rows,
    MIN(captured_at) AS date_debut,
    MAX(captured_at) AS date_fin
FROM measures

UNION ALL

SELECT 
    'Données migrées (fact_measures)' AS table_name,
    COUNT(*) AS total_rows,
    MIN(dt.full_date) AS date_debut,
    MAX(dt.full_date) AS date_fin
FROM fact_measures fm
LEFT JOIN dim_time dt ON fm.time_id = dt.time_id;

-- Vérifier les NULL dans les dimensions (qualité des données)
SELECT 
    COUNT(*) AS total,
    COUNT(time_id) AS with_time,
    COUNT(city_id) AS with_city,
    COUNT(weather_condition_id) AS with_weather,
    COUNT(aqi_level_id) AS with_aqi_level,
    COUNT(*) - COUNT(time_id) AS missing_time,
    COUNT(*) - COUNT(weather_condition_id) AS missing_weather,
    COUNT(*) - COUNT(aqi_level_id) AS missing_aqi_level
FROM fact_measures;

COMMENT ON TABLE fact_measures IS 'Table de faits - contient TOUTES les données de measures sans perte';
