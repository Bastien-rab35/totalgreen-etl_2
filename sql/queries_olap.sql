-- ============================================
-- REQUÊTES OLAP - ANALYSES MULTIDIMENSIONNELLES
-- Exemples d'utilisation du modèle en étoile
-- ============================================

-- ============================================
-- 1. ANALYSES TEMPORELLES
-- ============================================

-- Températures moyennes par mois et par ville (2025-2026)
SELECT 
    dc.city_name,
    dt.year,
    dt.month_name,
    ROUND(AVG(fm.temperature), 2) AS temp_moyenne,
    ROUND(AVG(fm.humidity), 2) AS humidite_moyenne,
    COUNT(*) AS nb_mesures
FROM fact_measures fm
JOIN dim_date dt ON fm.capture_date = dt.date_value
JOIN dim_city dc ON fm.city_id = dc.city_id
WHERE dt.year IN (2025, 2026)
GROUP BY dc.city_name, dt.year, dt.month, dt.month_name
ORDER BY dc.city_name, dt.year, dt.month;

-- Évolution horaire de la température (pattern journalier)
SELECT 
    fm.capture_hour,
    ROUND(AVG(fm.temperature), 2) AS temp_moyenne,
    ROUND(MIN(fm.temperature), 2) AS temp_min,
    ROUND(MAX(fm.temperature), 2) AS temp_max
FROM fact_measures fm
JOIN dim_date dt ON fm.capture_date = dt.date_value
GROUP BY fm.capture_hour
ORDER BY fm.capture_hour;

-- Comparaison weekend vs semaine
SELECT 
    CASE WHEN dt.is_weekend THEN 'Weekend' ELSE 'Semaine' END AS periode,
    ROUND(AVG(fm.aqi_index), 0) AS aqi_moyen,
    COUNT(*) AS nb_mesures
FROM fact_measures fm
JOIN dim_date dt ON fm.capture_date = dt.date_value
WHERE fm.aqi_index IS NOT NULL
GROUP BY dt.is_weekend;

-- ============================================
-- 2. ANALYSES GÉOGRAPHIQUES
-- ============================================

-- Classement des villes par qualité de l'air moyenne
SELECT 
    dc.city_name,
    dc.region,
    ROUND(AVG(fm.aqi_index), 0) AS aqi_moyen,
    ROUND(AVG(fm.pm25), 2) AS pm25_moyen,
    ROUND(AVG(fm.pm10), 2) AS pm10_moyen,
    COUNT(*) AS nb_mesures
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
WHERE fm.aqi_index IS NOT NULL
GROUP BY dc.city_name, dc.region
ORDER BY aqi_moyen ASC;

-- Villes les plus chaudes/froides
SELECT 
    'Plus chaude' AS type,
    dc.city_name,
    ROUND(MAX(fm.temperature), 2) AS temperature
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
GROUP BY dc.city_name
ORDER BY temperature DESC
LIMIT 1

UNION ALL

SELECT 
    'Plus froide' AS type,
    dc.city_name,
    ROUND(MIN(fm.temperature), 2) AS temperature
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
GROUP BY dc.city_name
ORDER BY temperature ASC
LIMIT 1;

-- ============================================
-- 3. ANALYSES PAR CONDITION MÉTÉO
-- ============================================

-- Distribution des conditions météo
SELECT 
    dwc.category,
    dwc.main,
    COUNT(*) AS occurrences,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pourcentage
FROM fact_measures fm
JOIN dim_weather_condition dwc ON fm.weather_condition_id = dwc.weather_condition_id
GROUP BY dwc.category, dwc.main
ORDER BY occurrences DESC;

-- Températures moyennes par type de temps
SELECT 
    dwc.category,
    ROUND(AVG(fm.temperature), 2) AS temp_moyenne,
    ROUND(AVG(fm.humidity), 2) AS humidite_moyenne,
    ROUND(AVG(fm.wind_speed), 2) AS vent_moyen
FROM fact_measures fm
JOIN dim_weather_condition dwc ON fm.weather_condition_id = dwc.weather_condition_id
GROUP BY dwc.category
ORDER BY temp_moyenne DESC;

-- ============================================
-- 4. ANALYSES QUALITÉ DE L'AIR PAR NIVEAU
-- ============================================

-- Répartition des niveaux AQI
SELECT 
    daql.level_name,
    daql.health_concern,
    COUNT(*) AS nb_mesures,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pourcentage
FROM fact_measures fm
JOIN dim_air_quality_level daql ON fm.aqi_level_id = daql.aqi_level_id
GROUP BY daql.aqi_level_id, daql.level_name, daql.health_concern
ORDER BY daql.aqi_level_id;

-- Villes avec le plus d'alertes pollution (AQI > 100)
SELECT 
    dc.city_name,
    daql.level_name,
    COUNT(*) AS nb_alertes,
    MIN(dt.full_date) AS premiere_alerte,
    MAX(dt.full_date) AS derniere_alerte
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_air_quality_level daql ON fm.aqi_level_id = daql.aqi_level_id
JOIN dim_date dt ON fm.capture_date = dt.date_value
WHERE daql.aqi_min > 100
GROUP BY dc.city_name, daql.level_name
ORDER BY nb_alertes DESC;

-- ============================================
-- 5. ANALYSES MULTIDIMENSIONNELLES COMPLEXES
-- ============================================

-- Cube OLAP : Ville x Mois x Niveau AQI
SELECT 
    dc.city_name,
    dt.month_name,
    daql.level_name,
    COUNT(*) AS nb_mesures,
    ROUND(AVG(fm.aqi_index), 0) AS aqi_moyen
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dt ON fm.capture_date = dt.date_value
JOIN dim_air_quality_level daql ON fm.aqi_level_id = daql.aqi_level_id
WHERE dt.year = 2026
GROUP BY CUBE(dc.city_name, dt.month, dt.month_name, daql.level_name)
ORDER BY dc.city_name NULLS FIRST, dt.month NULLS FIRST, daql.level_name NULLS FIRST;

-- Corrélation température / qualité de l'air par ville
SELECT 
    dc.city_name,
    ROUND(AVG(CASE WHEN fm.temperature < 10 THEN fm.aqi_index END), 0) AS aqi_froid,
    ROUND(AVG(CASE WHEN fm.temperature BETWEEN 10 AND 20 THEN fm.aqi_index END), 0) AS aqi_tempere,
    ROUND(AVG(CASE WHEN fm.temperature > 20 THEN fm.aqi_index END), 0) AS aqi_chaud
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
WHERE fm.aqi_index IS NOT NULL
GROUP BY dc.city_name
ORDER BY dc.city_name;

-- Tendance pollution par saison
SELECT 
    dt.season,
    ROUND(AVG(fm.pm25), 2) AS pm25_moyen,
    ROUND(AVG(fm.pm10), 2) AS pm10_moyen,
    ROUND(AVG(fm.no2), 2) AS no2_moyen,
    COUNT(*) AS nb_mesures
FROM fact_measures fm
JOIN dim_date dt ON fm.capture_date = dt.date_value
WHERE fm.pm25 IS NOT NULL
GROUP BY dt.season
ORDER BY 
    CASE dt.season
        WHEN 'Winter' THEN 1
        WHEN 'Spring' THEN 2
        WHEN 'Summer' THEN 3
        WHEN 'Fall' THEN 4
    END;

-- ============================================
-- 6. TABLEAUX DE BORD (KPIs)
-- ============================================

-- Dashboard global dernières 24h
WITH last_24h AS (
    SELECT * FROM fact_measures fm
    JOIN dim_date dt ON fm.capture_date = dt.date_value
    WHERE dt.full_date >= NOW() - INTERVAL '24 hours'
)
SELECT 
    'Température moyenne' AS kpi,
    ROUND(AVG(temperature), 2)::TEXT AS valeur,
    '°C' AS unite
FROM last_24h
UNION ALL
SELECT 
    'AQI moyen' AS kpi,
    ROUND(AVG(aqi_index), 0)::TEXT AS valeur,
    'index' AS unite
FROM last_24h
UNION ALL
SELECT 
    'Ville la plus polluée' AS kpi,
    dc.city_name AS valeur,
    ROUND(AVG(l.aqi_index), 0)::TEXT AS unite
FROM last_24h l
JOIN dim_city dc ON l.city_id = dc.city_id
GROUP BY dc.city_name
ORDER BY AVG(l.aqi_index) DESC
LIMIT 1;

-- Top 5 villes par température actuelle
SELECT 
    dc.city_name,
    ROUND(fm.temperature, 1) AS temperature,
    dwc.description AS meteo,
    fm.aqi_index
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dt ON fm.capture_date = dt.date_value
LEFT JOIN dim_weather_condition dwc ON fm.weather_condition_id = dwc.weather_condition_id
WHERE dt.full_date = (SELECT MAX(full_date) FROM dim_date WHERE full_date <= NOW())
ORDER BY fm.temperature DESC
LIMIT 5;

-- ============================================
-- 7. VUES MATÉRIALISÉES (Pour performances)
-- ============================================

-- Vue matérialisée : Moyennes mensuelles par ville
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_avg AS
SELECT 
    dc.city_id,
    dc.city_name,
    dt.year,
    dt.month,
    dt.month_name,
    ROUND(AVG(fm.temperature), 2) AS temp_avg,
    ROUND(AVG(fm.humidity), 2) AS humidity_avg,
    ROUND(AVG(fm.aqi_index), 0) AS aqi_avg,
    COUNT(*) AS measure_count
FROM fact_measures fm
JOIN dim_city dc ON fm.city_id = dc.city_id
JOIN dim_date dt ON fm.capture_date = dt.date_value
GROUP BY dc.city_id, dc.city_name, dt.year, dt.month, dt.month_name;

CREATE UNIQUE INDEX ON mv_monthly_avg (city_id, year, month);

-- Rafraîchir la vue (à lancer après chaque ETL)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_avg;

COMMENT ON MATERIALIZED VIEW mv_monthly_avg IS 'Vue pré-calculée pour analyses mensuelles rapides';
