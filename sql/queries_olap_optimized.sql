-- Requêtes OLAP Optimisées - GoodAir
-- Analyses analytiques pour rapports et dashboards

-- ========================================
-- 1. KPI Principaux par Ville (Quotidien)
-- ========================================
SELECT
    c.city_name,
    DATE(fm.captured_at) as date,
    ROUND(AVG(fm.aqi)::numeric, 1) as avg_aqi,
    ROUND(MAX(fm.aqi)::numeric, 0) as max_aqi,
    ROUND(AVG(fm.temperature)::numeric, 1) as avg_temp,
    ROUND(AVG(fm.pm2_5)::numeric, 1) as avg_pm25,
    COUNT(*) as measurements_count
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE fm.captured_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.city_name, DATE(fm.captured_at)
ORDER BY date DESC, avg_aqi DESC;

-- INDEX: Améliore performance
CREATE INDEX IF NOT EXISTS idx_fact_measures_date_city 
ON fact_measures(captured_at DESC, city_id) 
WHERE processed = true;

-- ========================================
-- 2. Corrélation: Température vs AQI
-- ========================================
WITH daily_agg AS (
    SELECT
        city_id,
        DATE(captured_at) as date,
        AVG(temperature) as avg_temp,
        AVG(aqi) as avg_aqi,
        AVG(humidity) as avg_humidity,
        AVG(pm2_5) as avg_pm25
    FROM fact_measures
    WHERE captured_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY city_id, DATE(captured_at)
)
SELECT
    (SELECT corr(avg_temp, avg_aqi) FROM daily_agg)::numeric(3,2) as corr_temp_aqi,
    (SELECT corr(avg_humidity, avg_aqi) FROM daily_agg)::numeric(3,2) as corr_humidity_aqi,
    (SELECT corr(avg_pm25, avg_aqi) FROM daily_agg)::numeric(3,2) as corr_pm25_aqi;

-- ========================================
-- 3. Alertes Dépassements de Seuils
-- ========================================
SELECT
    c.city_name,
    fm.captured_at,
    fm.aqi,
    fm.pm2_5,
    fm.temperature,
    CASE
        WHEN fm.aqi > 300 THEN 'CRITIQUE'
        WHEN fm.aqi > 200 THEN 'ÉLEVÉ'
        ELSE 'NORMAL'
    END as aqi_status,
    CASE
        WHEN fm.pm2_5 > 150 THEN 'ALERTE'
        WHEN fm.pm2_5 > 75 THEN 'PRÉALERTE'
        ELSE 'OK'
    END as pm25_status
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE (fm.aqi > 200 OR fm.pm2_5 > 75)
AND fm.captured_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY fm.captured_at DESC
LIMIT 1000;

-- ========================================
-- 4. Analyse Saisonnière: AQI par Mois
-- ========================================
SELECT
    c.city_name,
    EXTRACT(MONTH FROM fm.captured_at)::int as month,
    EXTRACT(YEAR FROM fm.captured_at)::int as year,
    ROUND(AVG(fm.aqi)::numeric, 1) as avg_aqi,
    ROUND(STDDEV(fm.aqi)::numeric, 1) as stddev_aqi,
    MIN(fm.aqi) as min_aqi,
    MAX(fm.aqi) as max_aqi,
    COUNT(*) as data_points
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE fm.captured_at >= DATE '2024-01-01'
GROUP BY c.city_name, EXTRACT(YEAR FROM fm.captured_at), EXTRACT(MONTH FROM fm.captured_at)
ORDER BY year DESC, month DESC, avg_aqi DESC;

-- ========================================
-- 5. Tableau Comparatif: Toutes les Villes
-- ========================================
SELECT
    c.city_name,
    c.latitude,
    c.longitude,
    -- Dernier enregistrement
    (SELECT aqi FROM fact_measures 
     WHERE city_id = c.city_id 
     ORDER BY captured_at DESC LIMIT 1) as latest_aqi,
    -- Stats 24h
    ROUND((SELECT AVG(aqi) FROM fact_measures 
           WHERE city_id = c.city_id 
           AND captured_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')::numeric, 1) as aqi_24h_avg,
    -- Stats 7j
    ROUND((SELECT AVG(aqi) FROM fact_measures 
           WHERE city_id = c.city_id 
           AND captured_at >= CURRENT_DATE - INTERVAL '7 days')::numeric, 1) as aqi_7d_avg,
    -- Qualité données
    COUNT(fm.fact_id) as total_measurements
FROM dim_city c
LEFT JOIN fact_measures fm ON c.city_id = fm.city_id
GROUP BY c.city_id, c.city_name, c.latitude, c.longitude
ORDER BY latest_aqi DESC NULLS LAST;

-- ========================================
-- 6. Cohérence Temporelle (Data QA)
-- ========================================
SELECT
    c.city_name,
    DATE(fm.captured_at) as date,
    COUNT(*) as hourly_count,
    (24 - COUNT(*)) as missing_hours,
    ROUND((COUNT(*) * 100.0 / 24)::numeric, 1) as completeness_percent,
    ROUND(AVG(fm.latence_ms)::numeric, 0) as avg_api_latency_ms
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE fm.captured_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY c.city_id, c.city_name, DATE(fm.captured_at)
HAVING COUNT(*) < 20  -- Alerter si moins de 20 mesures/jour
ORDER BY completeness_percent ASC;

-- ========================================
-- 7. Anomalies Détectées (Suivi QA)
-- ========================================
SELECT
    table_name,
    field_name,
    anomaly_type,
    severity,
    COUNT(*) as count,
    MAX(detected_at) as latest_detection
FROM anomalies
WHERE detected_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY table_name, field_name, anomaly_type, severity
ORDER BY severity DESC, count DESC;

-- ========================================
-- 8. Performance ETL (Monitoring)
-- ========================================
SELECT
    source,
    DATE(captured_at) as date,
    COUNT(*) as total_records,
    COUNT(CASE WHEN processed = true THEN 1 END) as processed_count,
    COUNT(CASE WHEN processed = false THEN 1 END) as pending_count,
    ROUND((COUNT(CASE WHEN processed = true THEN 1 END) * 100.0 / 
           COUNT(*))::numeric, 1) as processing_rate_percent,
    ROUND(AVG(latence_ms)::numeric, 0) as avg_latency_ms
FROM raw_data_lake
WHERE captured_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY source, DATE(captured_at)
ORDER BY date DESC;

-- ========================================
-- 9. Comparaison Villes: Variance Qualité
-- ========================================
SELECT
    c1.city_name as city1,
    c2.city_name as city2,
    ROUND(ABS(
        (SELECT AVG(aqi) FROM fact_measures WHERE city_id = c1.city_id 
         AND captured_at >= CURRENT_DATE - INTERVAL '7 days')
        -
        (SELECT AVG(aqi) FROM fact_measures WHERE city_id = c2.city_id 
         AND captured_at >= CURRENT_DATE - INTERVAL '7 days')
    )::numeric, 1) as aqi_difference
FROM dim_city c1
JOIN dim_city c2 ON c1.city_id < c2.city_id
ORDER BY aqi_difference DESC
LIMIT 10;

-- ========================================
-- 10. Export: Données Hourly (Dashboard)
-- ========================================
SELECT
    fm.captured_at AT TIME ZONE 'UTC' as timestamp_utc,
    c.city_name,
    c.latitude,
    c.longitude,
    fm.temperature,
    fm.humidity,
    fm.pressure,
    fm.aqi,
    fm.pm2_5,
    fm.pm10,
    fm.no2,
    fm.o3,
    fm.so2,
    fm.co,
    fm.wind_speed,
    fm.wind_gust,
    fm.clouds,
    fm.visibility,
    fm.uvi
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE fm.captured_at >= CURRENT_DATE - INTERVAL '3 days'
ORDER BY fm.captured_at DESC
LIMIT 100000;

-- ========================================
-- MATERIALIZED VIEW: Cache pour Dashboard
-- ========================================
-- Optionnel: Créer une vue matérialisée pour perf
CREATE MATERIALIZED VIEW IF NOT EXISTS v_dashboard_summary AS
SELECT
    c.city_name,
    c.latitude,
    c.longitude,
    DATE(fm.captured_at) as date,
    ROUND(AVG(fm.aqi)::numeric, 1) as avg_aqi,
    ROUND(MAX(fm.aqi)::numeric, 0) as max_aqi,
    ROUND(AVG(fm.temperature)::numeric, 1) as avg_temp,
    ROUND(AVG(fm.pm2_5)::numeric, 1) as avg_pm25,
    ROUND(AVG(fm.humidity)::numeric, 0) as avg_humidity,
    COUNT(*) as hourly_readings
FROM fact_measures fm
JOIN dim_city c ON fm.city_id = c.city_id
WHERE fm.captured_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.city_id, c.city_name, c.latitude, c.longitude, DATE(fm.captured_at);

-- Index sur vue matérialisée
CREATE INDEX IF NOT EXISTS idx_v_dashboard_city_date 
ON v_dashboard_summary(city_name, date DESC);

-- Rafraîchir tous les jours à minuit
-- COMMENT: Ajouter un job Cron: crontab -> 0 0 * * * psql -U user -d db -c "REFRESH MATERIALIZED VIEW v_dashboard_summary;"
