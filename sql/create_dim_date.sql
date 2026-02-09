-- ============================================
-- CRÉATION DE dim_date (dimension DATE simplifiée)
-- Remplace dim_time pour une architecture plus simple
-- ============================================

-- Créer la table dim_date
CREATE TABLE IF NOT EXISTS dim_date (
    date_value DATE PRIMARY KEY,  -- Clé primaire simple et lisible
    
    -- Jour
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0=Dimanche, 6=Samedi (PostgreSQL)
    day_name VARCHAR(10) NOT NULL,
    day_of_year INTEGER NOT NULL,
    
    -- Semaine
    week_of_year INTEGER NOT NULL,
    week_of_month INTEGER NOT NULL,
    
    -- Mois
    month INTEGER NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    
    -- Trimestre
    quarter INTEGER NOT NULL,
    quarter_name VARCHAR(10) NOT NULL,
    
    -- Année
    year INTEGER NOT NULL,
    
    -- Indicateurs
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    
    -- Saison
    season VARCHAR(10) NOT NULL
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_dim_date_value ON dim_date(date_value);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);
CREATE INDEX IF NOT EXISTS idx_dim_date_week ON dim_date(week_of_year);

COMMENT ON TABLE dim_date IS 'Dimension DATE - attributs temporels dérivés (sans heures)';

-- ============================================
-- REMPLIR dim_date avec toutes les dates 2024-2027
-- ============================================

INSERT INTO dim_date (
    date_value,
    day_of_month,
    day_of_week,
    day_name,
    day_of_year,
    week_of_year,
    week_of_month,
    month,
    month_name,
    quarter,
    quarter_name,
    year,
    is_weekend,
    season
)
SELECT 
    -- date_value (clé primaire)
    date_series::DATE,
    
    -- Jour
    EXTRACT(DAY FROM date_series)::INTEGER,
    EXTRACT(DOW FROM date_series)::INTEGER,  -- 0=Dimanche
    TO_CHAR(date_series, 'Day'),
    EXTRACT(DOY FROM date_series)::INTEGER,
    
    -- Semaine
    EXTRACT(WEEK FROM date_series)::INTEGER,
    CEILING(EXTRACT(DAY FROM date_series)::DECIMAL / 7)::INTEGER,
    
    -- Mois
    EXTRACT(MONTH FROM date_series)::INTEGER,
    TO_CHAR(date_series, 'Month'),
    
    -- Trimestre
    EXTRACT(QUARTER FROM date_series)::INTEGER,
    'Q' || EXTRACT(QUARTER FROM date_series)::TEXT,
    
    -- Année
    EXTRACT(YEAR FROM date_series)::INTEGER,
    
    -- Weekend
    EXTRACT(DOW FROM date_series) IN (0, 6),  -- Dimanche ou Samedi
    
    -- Saison (hémisphère nord)
    CASE 
        WHEN EXTRACT(MONTH FROM date_series) IN (12, 1, 2) THEN 'Hiver'
        WHEN EXTRACT(MONTH FROM date_series) IN (3, 4, 5) THEN 'Printemps'
        WHEN EXTRACT(MONTH FROM date_series) IN (6, 7, 8) THEN 'Été'
        ELSE 'Automne'
    END
FROM generate_series(
    '2024-01-01'::DATE,
    '2027-12-31'::DATE,
    '1 day'::INTERVAL
) AS date_series
ON CONFLICT (date_value) DO NOTHING;

-- ============================================
-- STATISTIQUES
-- ============================================

SELECT 
    'dim_date' as table_name,
    COUNT(*) as total_days,
    MIN(date_value) as first_date,
    MAX(date_value) as last_date,
    COUNT(*) FILTER (WHERE is_weekend) as weekend_days,
    COUNT(*) FILTER (WHERE NOT is_weekend) as weekdays
FROM dim_date;

-- Exemple de requête avec fact_measures
SELECT 
    dd.date_value,
    dd.day_name,
    dd.month_name,
    dd.is_weekend,
    COUNT(fm.measure_id) as nb_measures,
    ROUND(AVG(fm.temperature), 1) as avg_temp
FROM fact_measures fm
JOIN dim_date dd ON DATE(fm.captured_at) = dd.date_value
GROUP BY dd.date_value, dd.day_name, dd.month_name, dd.is_weekend
ORDER BY dd.date_value DESC
LIMIT 10;
