-- ============================================
-- AJOUT de la FK capture_date dans fact_measures
-- Lien formel avec dim_date (clé = date_value)
-- ============================================

-- Étape 1 : Ajouter la colonne capture_date
ALTER TABLE fact_measures 
ADD COLUMN IF NOT EXISTS capture_date DATE;

-- Étape 2 : Remplir capture_date à partir de captured_at
UPDATE fact_measures
SET capture_date = DATE(captured_at)
WHERE capture_date IS NULL;

-- Étape 3 : Vérifier que toutes les lignes sont remplies
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count 
    FROM fact_measures 
    WHERE capture_date IS NULL;
    
    IF null_count > 0 THEN
        RAISE NOTICE 'ATTENTION: % lignes avec capture_date NULL restantes', null_count;
    ELSE
        RAISE NOTICE 'SUCCESS: Toutes les lignes ont capture_date rempli';
    END IF;
END $$;

-- Étape 4 : Ajouter la contrainte NOT NULL
ALTER TABLE fact_measures 
ALTER COLUMN capture_date SET NOT NULL;

-- Étape 5 : Ajouter la clé étrangère vers dim_date
ALTER TABLE fact_measures
ADD CONSTRAINT fk_fact_measures_date
FOREIGN KEY (capture_date) REFERENCES dim_date(date_value);

-- Étape 6 : Ajouter un index
CREATE INDEX IF NOT EXISTS idx_fact_measures_capture_date 
ON fact_measures(capture_date);

-- Commentaire
COMMENT ON COLUMN fact_measures.capture_date IS 'FK vers dim_date.date_value (DATE uniquement)';

-- ============================================
-- VÉRIFICATION
-- ============================================

-- Statistiques
SELECT 
    'fact_measures' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT capture_date) as distinct_dates,
    MIN(capture_date) as oldest_date,
    MAX(capture_date) as newest_date
FROM fact_measures;

-- Test de jointure (simple et lisible)
SELECT 
    dd.date_value,
    dd.day_name,
    dd.season,
    COUNT(fm.measure_id) as nb_measures,
    ROUND(AVG(fm.temperature), 1) as avg_temp
FROM fact_measures fm
JOIN dim_date dd ON fm.capture_date = dd.date_value
GROUP BY dd.date_value, dd.day_name, dd.season
ORDER BY dd.date_value DESC
LIMIT 10;
