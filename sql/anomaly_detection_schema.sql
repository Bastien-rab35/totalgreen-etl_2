-- ===============================================
-- SCHÉMA DE DÉTECTION D'ANOMALIES
-- Pour le contrôle qualité ML des mesures
-- ===============================================

-- Table pour stocker les anomalies détectées
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    
    -- Référence à la mesure
    city_name VARCHAR(100) NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    
    -- Type d'anomalie détectée
    anomaly_type VARCHAR(50) NOT NULL,  -- 'business_rule', 'statistical', 'ml_isolation_forest'
    severity VARCHAR(20) NOT NULL,      -- 'low', 'medium', 'high', 'critical'
    
    -- Détails de l'anomalie
    field_name VARCHAR(50),             -- Champ concerné (temperature, aqi, etc.)
    actual_value NUMERIC,               -- Valeur mesurée
    expected_range_min NUMERIC,         -- Plage attendue min
    expected_range_max NUMERIC,         -- Plage attendue max
    
    -- Score ML
    anomaly_score NUMERIC,              -- Score d'anomalie (Isolation Forest: -1 à 1)
    
    -- Métadonnées
    description TEXT,
    action_taken VARCHAR(100),          -- 'rejected', 'flagged', 'accepted_with_warning'
    
    -- Audit
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index pour les recherches
    CONSTRAINT fk_city FOREIGN KEY (city_name) REFERENCES dim_city(city_name)
);

-- Index pour performances
CREATE INDEX idx_anomalies_city ON anomalies(city_name);
CREATE INDEX idx_anomalies_captured_at ON anomalies(captured_at);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);

-- Ajouter un champ de flag dans fact_measures
ALTER TABLE fact_measures 
ADD COLUMN IF NOT EXISTS is_anomaly BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS anomaly_score NUMERIC;

-- Commentaires
COMMENT ON TABLE anomalies IS 'Stocke les anomalies détectées par ML et règles métier';
COMMENT ON COLUMN anomalies.anomaly_type IS 'Type: business_rule (règles métier), statistical (Z-score/IQR), ml_isolation_forest';
COMMENT ON COLUMN anomalies.severity IS 'Gravité: low, medium, high, critical';
COMMENT ON COLUMN anomalies.anomaly_score IS 'Score Isolation Forest: plus négatif = plus anormal';
COMMENT ON COLUMN fact_measures.is_anomaly IS 'TRUE si la mesure est flaggée comme anomalie';
COMMENT ON COLUMN fact_measures.anomaly_score IS 'Score ML de l\'anomalie (si détectée)';

-- Vue pour analyser les anomalies
CREATE OR REPLACE VIEW v_anomalies_summary AS
SELECT 
    a.city_name,
    DATE(a.captured_at) as date,
    a.anomaly_type,
    a.severity,
    COUNT(*) as nb_anomalies,
    AVG(a.anomaly_score) as avg_anomaly_score,
    ARRAY_AGG(DISTINCT a.field_name) as affected_fields
FROM anomalies a
GROUP BY a.city_name, DATE(a.captured_at), a.anomaly_type, a.severity
ORDER BY date DESC, nb_anomalies DESC;

COMMENT ON VIEW v_anomalies_summary IS 'Résumé quotidien des anomalies par ville et type';

-- Vue pour les anomalies critiques récentes
CREATE OR REPLACE VIEW v_critical_anomalies AS
SELECT 
    a.anomaly_id,
    a.city_name,
    a.captured_at,
    a.anomaly_type,
    a.field_name,
    a.actual_value,
    a.expected_range_min,
    a.expected_range_max,
    a.anomaly_score,
    a.description,
    a.detected_at
FROM anomalies a
WHERE a.severity = 'critical'
  AND a.detected_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY a.detected_at DESC;

COMMENT ON VIEW v_critical_anomalies IS 'Anomalies critiques des 7 derniers jours';
