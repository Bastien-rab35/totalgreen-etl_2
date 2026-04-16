-- ============================================================
-- MSPR2 - Extensions schema pour TomTom (Traffic) + Hub'Eau
-- ============================================================
-- Objectif: ajouter des structures analytiques sans casser le schema existant.
-- Ce script s'appuie sur dim_city et dim_time deja presentes.

-- ==============================
-- 1) REFERENTIEL TRAFIC TOMTOM
-- ==============================

CREATE TABLE IF NOT EXISTS dim_traffic_point (
    traffic_point_id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES dim_city(city_id),
    code_point VARCHAR(100) NOT NULL,
    libelle_point VARCHAR(150) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    type_axe VARCHAR(50),
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (city_id, code_point)
);

CREATE INDEX IF NOT EXISTS idx_dim_traffic_point_city ON dim_traffic_point(city_id);
CREATE INDEX IF NOT EXISTS idx_dim_traffic_point_coords ON dim_traffic_point(latitude, longitude);

COMMENT ON TABLE dim_traffic_point IS 'Points TomTom par ville pour calcul de congestion representatif';

CREATE TABLE IF NOT EXISTS dim_incident_category (
    incident_category_id SERIAL PRIMARY KEY,
    icon_category INTEGER NOT NULL UNIQUE,
    libelle_category VARCHAR(80) NOT NULL
);

COMMENT ON TABLE dim_incident_category IS 'Categories incidents TomTom (iconCategory)';

INSERT INTO dim_incident_category (icon_category, libelle_category) VALUES
(0, 'Unknown'),
(1, 'Accident'),
(2, 'Fog'),
(3, 'DangerousConditions'),
(4, 'Rain'),
(5, 'Ice'),
(6, 'Jam'),
(7, 'LaneClosed'),
(8, 'RoadClosed'),
(9, 'RoadWorks'),
(10, 'Wind'),
(11, 'Flooding'),
(14, 'BrokenDownVehicle')
ON CONFLICT (icon_category) DO NOTHING;

-- =====================================
-- 2) FAITS TRAFIC - FLOW (HORAIRE)
-- =====================================

CREATE TABLE IF NOT EXISTS fact_traffic_flow_hourly (
    traffic_flow_id BIGSERIAL PRIMARY KEY,
    time_id INTEGER NOT NULL REFERENCES dim_time(time_id),
    city_id INTEGER NOT NULL REFERENCES dim_city(city_id),
    traffic_point_id INTEGER NOT NULL REFERENCES dim_traffic_point(traffic_point_id),

    vitesse_actuelle_kmph DECIMAL(7,2),
    vitesse_fluide_kmph DECIMAL(7,2),
    temps_trajet_actuel_s INTEGER,
    temps_trajet_fluide_s INTEGER,
    indice_confiance DECIMAL(5,4),
    route_fermee BOOLEAN,
    frc VARCHAR(10),

    -- KPIs derives
    congestion_ratio DECIMAL(8,4),
    speed_ratio DECIMAL(8,4),

    traffic_model_id VARCHAR(30),
    source_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (time_id, traffic_point_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_traffic_flow_time ON fact_traffic_flow_hourly(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_traffic_flow_city ON fact_traffic_flow_hourly(city_id);
CREATE INDEX IF NOT EXISTS idx_fact_traffic_flow_point ON fact_traffic_flow_hourly(traffic_point_id);

COMMENT ON TABLE fact_traffic_flow_hourly IS 'Mesures TomTom Flow par point et par heure';

-- ========================================
-- 3) FAITS TRAFIC - INCIDENTS (HORAIRE)
-- ========================================

CREATE TABLE IF NOT EXISTS fact_traffic_incident_hourly (
    traffic_incident_id BIGSERIAL PRIMARY KEY,
    time_id INTEGER NOT NULL REFERENCES dim_time(time_id),
    city_id INTEGER NOT NULL REFERENCES dim_city(city_id),
    incident_category_id INTEGER NOT NULL REFERENCES dim_incident_category(incident_category_id),

    nombre_incidents INTEGER NOT NULL DEFAULT 0,
    retard_total_s INTEGER DEFAULT 0,
    retard_moyen_s DECIMAL(10,2),
    longueur_moyenne_m DECIMAL(10,2),

    -- KPI metier: score pondere agrege sur la tranche horaire
    incident_severity_score DECIMAL(12,4),

    traffic_model_id VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (time_id, city_id, incident_category_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_traffic_incident_time ON fact_traffic_incident_hourly(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_traffic_incident_city ON fact_traffic_incident_hourly(city_id);

COMMENT ON TABLE fact_traffic_incident_hourly IS 'Pression incidents TomTom par ville et categorie';

-- ========================================
-- 4) REFERENTIEL HUB'EAU - STATIONS
-- ========================================

CREATE TABLE IF NOT EXISTS dim_groundwater_station (
    groundwater_station_id BIGSERIAL PRIMARY KEY,
    code_bss VARCHAR(50),
    bss_id VARCHAR(50),
    urn_bss VARCHAR(255),

    nom_station VARCHAR(255),
    code_commune_insee VARCHAR(10),
    nom_commune VARCHAR(120),
    code_departement VARCHAR(10),
    nom_departement VARCHAR(120),

    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    altitude_station_m DECIMAL(10,3),

    city_id_proche INTEGER REFERENCES dim_city(city_id),
    distance_city_km DECIMAL(8,3),

    nb_mesures_piezo INTEGER,
    date_debut_mesure DATE,
    date_fin_mesure DATE,
    date_maj TIMESTAMP WITH TIME ZONE,

    actif BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (code_bss),
    UNIQUE (bss_id)
);

CREATE INDEX IF NOT EXISTS idx_dim_groundwater_station_city ON dim_groundwater_station(city_id_proche);
CREATE INDEX IF NOT EXISTS idx_dim_groundwater_station_dept ON dim_groundwater_station(code_departement);

COMMENT ON TABLE dim_groundwater_station IS 'Referentiel stations piezometriques Hub''Eau';

-- ======================================
-- 5) FAITS HUB'EAU - CHRONIQUES JOUR
-- ======================================

CREATE TABLE IF NOT EXISTS fact_groundwater_daily (
    groundwater_daily_id BIGSERIAL PRIMARY KEY,
    measure_date DATE NOT NULL,
    groundwater_station_id BIGINT NOT NULL REFERENCES dim_groundwater_station(groundwater_station_id),

    groundwater_level_ngf_m DECIMAL(12,4),
    groundwater_depth_m DECIMAL(12,4),

    statut_mesure VARCHAR(80),
    qualification_mesure VARCHAR(80),
    mode_obtention VARCHAR(80),

    code_producteur VARCHAR(80),
    nom_producteur VARCHAR(255),

    source_timestamp BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (measure_date, groundwater_station_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_groundwater_daily_date ON fact_groundwater_daily(measure_date);
CREATE INDEX IF NOT EXISTS idx_fact_groundwater_daily_station ON fact_groundwater_daily(groundwater_station_id);

COMMENT ON TABLE fact_groundwater_daily IS 'Serie historique quotidienne niveaux/profondeurs des nappes';

-- ==========================================
-- 6) FAITS HUB'EAU - CHRONIQUES TEMPS REEL
-- ==========================================

CREATE TABLE IF NOT EXISTS fact_groundwater_realtime (
    groundwater_realtime_id BIGSERIAL PRIMARY KEY,
    time_id INTEGER NOT NULL REFERENCES dim_time(time_id),
    groundwater_station_id BIGINT NOT NULL REFERENCES dim_groundwater_station(groundwater_station_id),

    groundwater_level_ngf_m DECIMAL(12,4),
    groundwater_depth_m DECIMAL(12,4),

    altitude_repere_m DECIMAL(12,4),
    altitude_station_m DECIMAL(12,4),

    date_maj TIMESTAMP WITH TIME ZONE,
    source_timestamp BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (time_id, groundwater_station_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_groundwater_rt_time ON fact_groundwater_realtime(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_groundwater_rt_station ON fact_groundwater_realtime(groundwater_station_id);

COMMENT ON TABLE fact_groundwater_realtime IS 'Chroniques Hub''Eau quasi temps reel';

-- ==========================================
-- 7) VUE KPI NAPPE: TENDANCE 7 JOURS + ANOMALIE
-- ==========================================

CREATE OR REPLACE VIEW vw_groundwater_daily_kpi AS
SELECT
    d.groundwater_daily_id,
    d.groundwater_station_id,
    d.measure_date,
    d.groundwater_level_ngf_m,
    d.groundwater_depth_m,
    AVG(d.groundwater_level_ngf_m) OVER (
        PARTITION BY d.groundwater_station_id
        ORDER BY d.measure_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS groundwater_trend_7d,
    CASE
        WHEN STDDEV_SAMP(d.groundwater_level_ngf_m) OVER (
            PARTITION BY d.groundwater_station_id
            ORDER BY d.measure_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) IS NULL THEN NULL
        WHEN STDDEV_SAMP(d.groundwater_level_ngf_m) OVER (
            PARTITION BY d.groundwater_station_id
            ORDER BY d.measure_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) = 0 THEN 0
        ELSE (
            d.groundwater_level_ngf_m - AVG(d.groundwater_level_ngf_m) OVER (
                PARTITION BY d.groundwater_station_id
                ORDER BY d.measure_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            )
        ) / NULLIF(
            STDDEV_SAMP(d.groundwater_level_ngf_m) OVER (
                PARTITION BY d.groundwater_station_id
                ORDER BY d.measure_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ),
            0
        )
    END AS anomaly_score
FROM fact_groundwater_daily d;

COMMENT ON VIEW vw_groundwater_daily_kpi IS 'KPI derives: tendance 7 jours et score d anomalie glissant';
