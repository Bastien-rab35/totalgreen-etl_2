-- ============================================
-- Requêtes SQL utiles pour l'analyse des données
-- TotalGreen - Projet de surveillance environnementale
-- ============================================

-- 1. Vue d'ensemble des dernières mesures
SELECT 
    c.name AS ville,
    m.captured_at,
    m.temp AS "température_°C",
    m.humidity AS "humidité_%",
    m.wind_speed AS "vent_m/s",
    m.aqi_index AS "AQI",
    m.pm25 AS "PM2.5",
    m.weather_description AS "météo"
FROM measures m
JOIN cities c ON m.city_id = c.id
ORDER BY m.captured_at DESC
LIMIT 50;

-- 2. Dernière mesure pour chaque ville
SELECT DISTINCT ON (c.name)
    c.name AS ville,
    m.captured_at,
    m.temp,
    m.aqi_index,
    m.pm25
FROM measures m
JOIN cities c ON m.city_id = c.id
ORDER BY c.name, m.captured_at DESC;

-- 3. Corrélation Vent vs Pollution (PM2.5)
SELECT 
    c.name AS ville,
    AVG(m.wind_speed) AS "vent_moyen_m/s",
    AVG(m.pm25) AS "PM2.5_moyen",
    CORR(m.wind_speed, m.pm25) AS "corrélation"
FROM measures m
JOIN cities c ON m.city_id = c.id
WHERE m.wind_speed IS NOT NULL AND m.pm25 IS NOT NULL
GROUP BY c.name
ORDER BY "corrélation" DESC;

-- 4. Évolution de la température sur 24h (Paris)
SELECT 
    DATE_TRUNC('hour', captured_at) AS heure,
    AVG(temp) AS temp_moyenne,
    MIN(temp) AS temp_min,
    MAX(temp) AS temp_max
FROM measures
WHERE city_id = 1  -- Paris
  AND captured_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', captured_at)
ORDER BY heure;

-- 5. Statistiques de qualité de l'air par ville
SELECT 
    c.name AS ville,
    COUNT(*) AS "nb_mesures",
    AVG(m.aqi_index) AS "AQI_moyen",
    MIN(m.aqi_index) AS "AQI_min",
    MAX(m.aqi_index) AS "AQI_max",
    STDDEV(m.aqi_index) AS "écart_type"
FROM measures m
JOIN cities c ON m.city_id = c.id
WHERE m.aqi_index IS NOT NULL
GROUP BY c.name
ORDER BY "AQI_moyen" DESC;

-- 6. Villes les plus polluées (PM2.5 moyen)
SELECT 
    c.name AS ville,
    AVG(m.pm25) AS "PM2.5_moyen_μg/m³",
    CASE 
        WHEN AVG(m.pm25) <= 12 THEN 'Bon'
        WHEN AVG(m.pm25) <= 35 THEN 'Modéré'
        WHEN AVG(m.pm25) <= 55 THEN 'Mauvais'
        ELSE 'Très mauvais'
    END AS qualité
FROM measures m
JOIN cities c ON m.city_id = c.id
WHERE m.pm25 IS NOT NULL
GROUP BY c.name
ORDER BY "PM2.5_moyen_μg/m³" DESC;

-- 7. Logs ETL - Historique des exécutions
SELECT 
    execution_time,
    status,
    records_inserted,
    execution_duration_seconds AS "durée_s",
    error_message
FROM etl_logs
ORDER BY execution_time DESC
LIMIT 50;

-- 8. Taux de réussite du pipeline ETL
SELECT 
    status,
    COUNT(*) AS nombre,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pourcentage
FROM etl_logs
GROUP BY status
ORDER BY nombre DESC;

-- 9. Export pour analyse R/Excel (CSV format)
COPY (
    SELECT 
        c.name AS ville,
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
        m.no2,
        m.o3,
        m.weather_main,
        m.weather_description
    FROM measures m
    JOIN cities c ON m.city_id = c.id
    WHERE m.captured_at >= NOW() - INTERVAL '7 days'
    ORDER BY m.captured_at DESC
) TO '/tmp/totalgreen_export.csv' CSV HEADER;

-- 10. Détection des anomalies (températures extrêmes)
SELECT 
    c.name AS ville,
    m.captured_at,
    m.temp,
    m.weather_description
FROM measures m
JOIN cities c ON m.city_id = c.id
WHERE m.temp < -10 OR m.temp > 40
ORDER BY m.temp DESC;

-- 11. Moyenne mobile sur 3 heures (température Paris)
SELECT 
    captured_at,
    temp,
    AVG(temp) OVER (
        ORDER BY captured_at 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS temp_moyenne_mobile_3h
FROM measures
WHERE city_id = 1
ORDER BY captured_at DESC
LIMIT 24;

-- 12. Comparaison inter-villes (dernière heure)
SELECT 
    c.name AS ville,
    m.temp AS "temp_°C",
    m.humidity AS "humid_%",
    m.aqi_index AS "AQI",
    m.captured_at
FROM measures m
JOIN cities c ON m.city_id = c.id
WHERE m.captured_at >= NOW() - INTERVAL '1 hour'
ORDER BY m.temp DESC;
