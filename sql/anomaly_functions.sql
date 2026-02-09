-- ===============================================
-- FONCTIONS UTILITAIRES POUR DÉTECTION D'ANOMALIES
-- ===============================================

-- Fonction pour calculer les statistiques d'une ville
CREATE OR REPLACE FUNCTION get_city_stats(
    p_city_name VARCHAR,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    field_name TEXT,
    mean_value NUMERIC,
    std_value NUMERIC,
    min_value NUMERIC,
    max_value NUMERIC,
    count_values BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH city_measures AS (
        SELECT 
            fm.temperature,
            fm.humidity,
            fm.pressure,
            fm.aqi
        FROM fact_measures fm
        JOIN dim_city dc ON fm.city_id = dc.city_id
        JOIN dim_time dt ON fm.time_id = dt.time_id
        WHERE dc.city_name = p_city_name
          AND dt.date_full >= CURRENT_DATE - p_days
          AND fm.is_anomaly IS NOT TRUE  -- Exclure les anomalies connues
    )
    SELECT 
        'temperature'::TEXT,
        AVG(temperature),
        STDDEV(temperature),
        MIN(temperature),
        MAX(temperature),
        COUNT(temperature)
    FROM city_measures
    WHERE temperature IS NOT NULL
    UNION ALL
    SELECT 
        'humidity'::TEXT,
        AVG(humidity),
        STDDEV(humidity),
        MIN(humidity),
        MAX(humidity),
        COUNT(humidity)
    FROM city_measures
    WHERE humidity IS NOT NULL
    UNION ALL
    SELECT 
        'pressure'::TEXT,
        AVG(pressure),
        STDDEV(pressure),
        MIN(pressure),
        MAX(pressure),
        COUNT(pressure)
    FROM city_measures
    WHERE pressure IS NOT NULL
    UNION ALL
    SELECT 
        'aqi'::TEXT,
        AVG(aqi),
        STDDEV(aqi),
        MIN(aqi),
        MAX(aqi),
        COUNT(aqi)
    FROM city_measures
    WHERE aqi IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_city_stats IS 'Calcule les statistiques (mean, std, min, max) pour une ville sur N jours';

-- Fonction pour obtenir un résumé des anomalies
CREATE OR REPLACE FUNCTION get_anomaly_summary(
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    city_name VARCHAR,
    total_anomalies BIGINT,
    critical_count BIGINT,
    high_count BIGINT,
    medium_count BIGINT,
    low_count BIGINT,
    business_rule_count BIGINT,
    statistical_count BIGINT,
    ml_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.city_name,
        COUNT(*) as total_anomalies,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
        COUNT(*) FILTER (WHERE severity = 'high') as high_count,
        COUNT(*) FILTER (WHERE severity = 'medium') as medium_count,
        COUNT(*) FILTER (WHERE severity = 'low') as low_count,
        COUNT(*) FILTER (WHERE anomaly_type = 'business_rule') as business_rule_count,
        COUNT(*) FILTER (WHERE anomaly_type = 'statistical') as statistical_count,
        COUNT(*) FILTER (WHERE anomaly_type = 'ml_isolation_forest') as ml_count
    FROM anomalies a
    WHERE a.detected_at >= CURRENT_TIMESTAMP - (p_days || ' days')::INTERVAL
    GROUP BY a.city_name
    ORDER BY total_anomalies DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_anomaly_summary IS 'Résumé des anomalies par ville sur N jours';
