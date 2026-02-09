-- ============================================
-- NETTOYAGE DES TABLES OBSOLÈTES
-- Supprime les anciennes tables du modèle normalisé
-- maintenant remplacées par le modèle en étoile
-- ============================================

-- ============================================
-- VÉRIFICATION AVANT SUPPRESSION
-- ============================================

-- Compter les enregistrements pour vérifier qu'on ne perd rien
DO $$
DECLARE
    count_measures INTEGER;
    count_fact INTEGER;
    count_cities INTEGER;
    count_dim_city INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_measures FROM measures WHERE TRUE;
    SELECT COUNT(*) INTO count_fact FROM fact_measures WHERE TRUE;
    SELECT COUNT(*) INTO count_cities FROM cities WHERE TRUE;
    SELECT COUNT(*) INTO count_dim_city FROM dim_city WHERE TRUE;
    
    RAISE NOTICE '================================';
    RAISE NOTICE 'VÉRIFICATION AVANT SUPPRESSION';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Mesures dans measures (ancien): %', count_measures;
    RAISE NOTICE 'Mesures dans fact_measures (nouveau): %', count_fact;
    RAISE NOTICE 'Villes dans cities (ancien): %', count_cities;
    RAISE NOTICE 'Villes dans dim_city (nouveau): %', count_dim_city;
    
    IF count_fact = 0 AND count_measures > 0 THEN
        RAISE EXCEPTION 'ATTENTION: fact_measures est vide mais measures contient des données! Migration nécessaire.';
    END IF;
    
    IF count_dim_city = 0 AND count_cities > 0 THEN
        RAISE EXCEPTION 'ATTENTION: dim_city est vide mais cities contient des données! Migration nécessaire.';
    END IF;
    
    RAISE NOTICE '✓ Vérification OK - Prêt pour suppression';
END $$;

-- ============================================
-- SUPPRESSION DE LA TABLE MEASURES (ANCIEN MODÈLE)
-- ============================================

-- Sauvegarder le nombre d'enregistrements pour référence
CREATE TEMP TABLE migration_stats AS
SELECT 
    (SELECT COUNT(*) FROM measures) AS old_measures,
    (SELECT COUNT(*) FROM fact_measures) AS new_fact_measures,
    (SELECT COUNT(*) FROM cities) AS old_cities,
    (SELECT COUNT(*) FROM dim_city) AS new_dim_cities;

-- Supprimer les anciennes tables
DROP TABLE IF EXISTS measures CASCADE;
DROP TABLE IF EXISTS cities CASCADE;

COMMENT ON TABLE fact_measures IS 'Table de faits principale - Remplace la table measures depuis le 2026-02-09';
COMMENT ON TABLE dim_city IS 'Dimension ville - Remplace la table cities depuis le 2026-02-09';

-- ============================================
-- RAPPORT FINAL
-- =====measures INTEGER;
    new_measures INTEGER;
    old_cities INTEGER;
    new_cities INTEGER;
BEGIN
    SELECT old_measures, new_fact_measures, old_cities, new_dim_cities 
    INTO old_measures, new_measures, old_cities, new_cities 
    FROM migration_stats;
    
    RAISE NOTICE '================================';
    RAISE NOTICE 'NETTOYAGE TERMINÉ';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Ancien modèle (measures): % enregistrements → SUPPRIMÉ', old_measures;
    RAISE NOTICE 'Nouveau modèle (fact_measures): % enregistrements → ACTIF', new_measures;
    RAISE NOTICE 'Ancien référentiel (cities): % enregistrements → SUPPRIMÉ', old_cities;
    RAISE NOTICE 'Nouvelle dimension (dim_city): % enregistrements → ACTIF', new_cities;
    RAISE NOTICE '';
    RAISE NOTICE '✓ Tables conservées:';
    RAISE NOTICE '  - raw_data_lake (data lake)';
    RAISE NOTICE '  - etl_logs (traçabilité)';
    RAISE NOTICE '  - dim_time, dim_city, dim_weather_condition, dim_air_quality_level (dimensions)';
    RAISE NOTICE '  - fact_measures (table de faits)';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Tables supprimées:';
    RAISE NOTICE '  - measures (remplacée par fact_measures)';
    RAISE NOTICE '  - cities (remplacée par dim_citytion, dim_air_quality_level (dimensions)';
    RAISE NOTICE '  - fact_measures (table de faits)';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Tables supprimées:';
    RAISE NOTICE '  - measures (remplacée par fact_measures)';
END $$;

-- Nettoyer la table temporaire
DROP TABLE migration_stats;

-- ============================================
-- VACUUM POUR RÉCUPÉRER L'ESPACE DISQUE
-- ============================================
-- Note: VACUUM FULL doit être exécuté séparément (pas dans une transaction)
-- Exécutez cette commande manuellement après le nettoyage:
-- VACUUM FULL;
