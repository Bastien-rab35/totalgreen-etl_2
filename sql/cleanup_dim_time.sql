-- ============================================
-- NETTOYAGE : Suppression de dim_time et time_id
-- Architecture simplifiée utilise capture_date + dim_date
-- ============================================

-- Étape 1 : Supprimer la colonne time_id de fact_measures
ALTER TABLE fact_measures 
DROP COLUMN IF EXISTS time_id CASCADE;

-- Étape 2 : Supprimer la table dim_time
DROP TABLE IF EXISTS dim_time CASCADE;

-- Commentaires
COMMENT ON TABLE fact_measures IS 'Table de faits - mesures environnementales (utilise capture_date vers dim_date)';

-- ============================================
-- VÉRIFICATION
-- ============================================

-- Vérifier que time_id n'existe plus dans fact_measures
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'fact_measures' 
ORDER BY ordinal_position;

-- Vérifier que dim_time n'existe plus
SELECT 
    table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name = 'dim_time';
-- Devrait retourner 0 ligne

-- Vérifier les tables restantes
SELECT 
    table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ============================================
-- STATISTIQUES POST-NETTOYAGE
-- ============================================

SELECT 
    'fact_measures' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT capture_date) as distinct_dates,
    MIN(capture_date) as oldest_date,
    MAX(capture_date) as newest_date
FROM fact_measures;

-- Test jointure avec dim_date
SELECT 
    dd.date_value,
    dd.day_name,
    dd.season,
    COUNT(fm.measure_id) as nb_measures
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
GROUP BY dd.date_value, dd.day_name, dd.season
ORDER BY dd.date_value DESC
LIMIT 5;
