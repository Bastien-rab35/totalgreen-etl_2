-- ============================================
-- MIGRATION : Ajouter captured_at dans fact_measures
-- Convertir de time_id vers timestamp direct
-- ============================================

-- Étape 1 : Ajouter la colonne captured_at (NULL autorisé temporairement)
ALTER TABLE fact_measures 
ADD COLUMN IF NOT EXISTS captured_at TIMESTAMP WITH TIME ZONE;

-- Étape 2 : Remplir captured_at à partir de dim_time.full_date
UPDATE fact_measures fm
SET captured_at = dt.full_date
FROM dim_time dt
WHERE fm.time_id = dt.time_id
  AND fm.captured_at IS NULL;

-- Étape 3 : Vérifier que toutes les lignes sont remplies
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count 
    FROM fact_measures 
    WHERE captured_at IS NULL;
    
    IF null_count > 0 THEN
        RAISE NOTICE 'ATTENTION: % lignes avec captured_at NULL restantes', null_count;
    ELSE
        RAISE NOTICE 'SUCCESS: Toutes les lignes ont captured_at rempli';
    END IF;
END $$;

-- Étape 4 : Ajouter la contrainte NOT NULL
ALTER TABLE fact_measures 
ALTER COLUMN captured_at SET NOT NULL;

-- Étape 5 : Ajouter un index sur captured_at pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_fact_measures_captured_at 
ON fact_measures(captured_at DESC);

-- Étape 6 : Ajouter un index composite ville + date
CREATE INDEX IF NOT EXISTS idx_fact_measures_city_captured 
ON fact_measures(city_id, captured_at DESC);

-- Commentaire
COMMENT ON COLUMN fact_measures.captured_at IS 'Timestamp exact de la mesure (remplace la FK time_id)';

-- ============================================
-- STATISTIQUES POST-MIGRATION
-- ============================================

-- Afficher les statistiques
SELECT 
    'fact_measures' as table_name,
    COUNT(*) as total_rows,
    MIN(captured_at) as oldest_measure,
    MAX(captured_at) as newest_measure,
    COUNT(DISTINCT DATE(captured_at)) as distinct_days
FROM fact_measures;

-- Vérifier la distribution par heure
SELECT 
    EXTRACT(HOUR FROM captured_at) as hour,
    COUNT(*) as count
FROM fact_measures
GROUP BY EXTRACT(HOUR FROM captured_at)
ORDER BY hour;
