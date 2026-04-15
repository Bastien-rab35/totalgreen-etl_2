-- =====================================================
-- Table de stockage des anomalies détectées
-- =====================================================
-- Stocke les anomalies détectées par validate_data_quality.py
-- Permet de tracer l'historique des problèmes de qualité des données

-- Table anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    validation_run_id UUID NOT NULL,      -- Identifiant unique du run de validation
    severity VARCHAR(20) NOT NULL,         -- critical, warning, info
    category VARCHAR(100) NOT NULL,        -- Catégorie (data_missing, duplicates, temporal_coherence, etc.)
    message TEXT NOT NULL,                 -- Description du problème
    details JSONB,                         -- Détails supplémentaires (exemples, statistiques, etc.)
    detected_at TIMESTAMPTZ NOT NULL,      -- Timestamp de détection
    validation_period_hours INT,           -- Période analysée (en heures)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Contraintes
    CHECK (severity IN ('critical', 'warning', 'info'))
);

-- Index pour recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_anomalies_validation_run ON anomalies(validation_run_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_category ON anomalies(category);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_created_at ON anomalies(created_at DESC);

-- Vue pour statistiques quotidiennes
CREATE OR REPLACE VIEW anomalies_daily_stats AS
SELECT 
    DATE(detected_at) as date,
    severity,
    category,
    COUNT(*) as count,
    COUNT(DISTINCT validation_run_id) as validation_runs
FROM anomalies
GROUP BY DATE(detected_at), severity, category
ORDER BY date DESC, severity, count DESC;

-- Commentaires
COMMENT ON TABLE anomalies IS 'Stocke les anomalies de qualité détectées par validate_data_quality.py';
COMMENT ON COLUMN anomalies.validation_run_id IS 'UUID unique pour regrouper les anomalies d''un même run de validation';
COMMENT ON COLUMN anomalies.severity IS 'Niveau de gravité: critical (bloquant), warning (à surveiller), info (informatif)';
COMMENT ON COLUMN anomalies.category IS 'Catégorie de l''anomalie (data_missing, duplicates, temporal_coherence, business_rules, etc.)';
COMMENT ON COLUMN anomalies.details IS 'Détails au format JSON (exemples, statistiques, liste des villes impactées, etc.)';
COMMENT ON COLUMN anomalies.validation_period_hours IS 'Période analysée lors de la validation (24h, 48h, etc.)';
