-- ============================================
-- Requêtes d'analyse du Data Lake
-- ============================================

-- 1. Vue d'ensemble du Data Lake
SELECT 
    source,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN processed THEN 1 END) AS processed,
    COUNT(CASE WHEN NOT processed THEN 1 END) AS pending,
    MIN(collected_at) AS oldest,
    MAX(collected_at) AS newest
FROM raw_data_lake
GROUP BY source;

-- 2. Données brutes récentes (JSONB)
SELECT 
    id,
    city_name,
    source,
    raw_data,
    collected_at,
    processed
FROM raw_data_lake
ORDER BY collected_at DESC
LIMIT 10;

-- 3. Recherche dans le JSONB (exemple: température > 25°C)
SELECT 
    city_name,
    collected_at,
    raw_data->'main'->>'temp' AS temperature,
    raw_data->'weather'->0->>'description' AS weather
FROM raw_data_lake
WHERE source = 'openweather'
  AND (raw_data->'main'->>'temp')::float > 25
ORDER BY collected_at DESC;

-- 4. Recherche dans le JSONB (AQI élevé > 100)
SELECT 
    city_name,
    collected_at,
    raw_data->'data'->>'aqi' AS aqi_index,
    raw_data->'data'->'city'->>'name' AS station
FROM raw_data_lake
WHERE source = 'aqicn'
  AND (raw_data->'data'->>'aqi')::int > 100
ORDER BY collected_at DESC;

-- 5. Traçabilité: Données brutes → Données transformées
SELECT 
    m.id AS measure_id,
    m.captured_at,
    c.name AS city,
    m.temp AS transformed_temp,
    rdl_weather.raw_data->'main'->>'temp' AS raw_temp,
    m.aqi_index AS transformed_aqi,
    rdl_aqi.raw_data->'data'->>'aqi' AS raw_aqi
FROM measures m
JOIN cities c ON m.city_id = c.id
LEFT JOIN raw_data_lake rdl_weather ON m.raw_weather_id = rdl_weather.id
LEFT JOIN raw_data_lake rdl_aqi ON m.raw_aqi_id = rdl_aqi.id
ORDER BY m.captured_at DESC
LIMIT 20;

-- 6. Export JSONB complet pour une ville
SELECT 
    jsonb_build_object(
        'city', city_name,
        'source', source,
        'collected_at', collected_at,
        'data', raw_data
    ) AS export
FROM raw_data_lake
WHERE city_name = 'Paris'
  AND collected_at >= NOW() - INTERVAL '24 hours'
ORDER BY collected_at DESC;

-- 7. Statistiques de collecte par ville et source
SELECT 
    city_name,
    source,
    COUNT(*) AS nb_collections,
    MAX(collected_at) AS derniere_collecte,
    AVG(EXTRACT(EPOCH FROM (collected_at - LAG(collected_at) OVER (PARTITION BY city_name, source ORDER BY collected_at)))) / 60 AS intervalle_moyen_minutes
FROM raw_data_lake
GROUP BY city_name, source
ORDER BY city_name, source;

-- 8. Données non traitées (pour retraitement)
SELECT 
    id,
    city_name,
    source,
    collected_at,
    raw_data
FROM raw_data_lake
WHERE processed = FALSE
ORDER BY collected_at ASC;

-- 9. Audit de transformation (différences raw vs transformed)
WITH raw_temps AS (
    SELECT 
        id,
        city_name,
        (raw_data->'main'->>'temp')::float AS raw_temp,
        collected_at
    FROM raw_data_lake
    WHERE source = 'openweather'
      AND collected_at >= NOW() - INTERVAL '1 hour'
)
SELECT 
    rt.city_name,
    rt.raw_temp,
    m.temp AS transformed_temp,
    ABS(rt.raw_temp - m.temp) AS difference,
    rt.collected_at
FROM raw_temps rt
LEFT JOIN measures m ON m.raw_weather_id = rt.id
WHERE ABS(rt.raw_temp - m.temp) > 0.1
ORDER BY difference DESC;

-- 10. Purge des anciennes données (> 30 jours)
-- À UTILISER AVEC PRÉCAUTION
-- DELETE FROM raw_data_lake 
-- WHERE collected_at < NOW() - INTERVAL '30 days' 
-- AND processed = TRUE;
