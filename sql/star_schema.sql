-- ============================================
-- MODÈLE EN ÉTOILE (STAR SCHEMA)
-- Data Warehouse pour analyses OLAP
-- ============================================

-- ============================================
-- TABLES DE DIMENSIONS
-- ============================================

-- Dimension Temps (architecture cible avec dim_date au lieu de dim_time)
CREATE TABLE IF NOT EXISTS dim_date (
    date_value DATE PRIMARY KEY,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    week_of_month INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter INTEGER NOT NULL,
    quarter_name VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    season VARCHAR(10) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_date_value ON dim_date(date_value);
CREATE INDEX IF NOT EXISTS idx_dim_date_week ON dim_date(week_of_year);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);

COMMENT ON TABLE dim_date IS 'Dimension date - permet analyses par période journalière';

-- Dimension Ville (hérite de cities existante)
CREATE TABLE IF NOT EXISTS dim_city (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    timezone VARCHAR(50),
    region VARCHAR(100),
    country VARCHAR(100) DEFAULT 'France',
    population INTEGER,
    altitude DECIMAL(7,2)
);

CREATE INDEX idx_dim_city_name ON dim_city(city_name);

COMMENT ON TABLE dim_city IS 'Dimension géographique - caractéristiques des villes';

-- Dimension Conditions Météo
CREATE TABLE IF NOT EXISTS dim_weather_condition (
    weather_condition_id SERIAL PRIMARY KEY,
    weather_id INTEGER UNIQUE, -- Code OpenWeather (ex: 800)
    main VARCHAR(50), -- Clear, Clouds, Rain...
    description VARCHAR(100), -- clear sky, few clouds...
    category VARCHAR(20), -- sunny, cloudy, rainy, stormy
    icon VARCHAR(10)
);

CREATE INDEX idx_dim_weather_main ON dim_weather_condition(main);

COMMENT ON TABLE dim_weather_condition IS 'Dimension météo - types de conditions';

-- Dimension Niveau Qualité de l\'Air
CREATE TABLE IF NOT EXISTS dim_air_quality_level (
    aqi_level_id SERIAL PRIMARY KEY,
    aqi_min INTEGER NOT NULL,
    aqi_max INTEGER NOT NULL,
    level_name VARCHAR(50) NOT NULL, -- Good, Moderate, Unhealthy...
    health_concern VARCHAR(100),
    color_code VARCHAR(20),
    health_advice TEXT
);

CREATE INDEX idx_dim_aqi_range ON dim_air_quality_level(aqi_min, aqi_max);

COMMENT ON TABLE dim_air_quality_level IS 'Dimension AQI - niveaux de qualité air';

-- ============================================
-- TABLE DE FAITS (FACT TABLE)
-- ============================================

-- Fait Mesures - Table centrale du modèle en étoile
CREATE TABLE IF NOT EXISTS fact_measures (
    measure_id BIGSERIAL PRIMARY KEY,
    
    -- Clés étrangères vers dimensions
    capture_date DATE NOT NULL REFERENCES dim_date(date_value),
    capture_hour INTEGER NOT NULL,
    capture_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    city_id INTEGER REFERENCES dim_city(city_id),
    weather_condition_id INTEGER REFERENCES dim_weather_condition(weather_condition_id),
    aqi_level_id INTEGER REFERENCES dim_air_quality_level(aqi_level_id),
    
    -- Métriques météo (mesures quantitatives)
    temperature DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    pressure INTEGER,
    humidity INTEGER,
    wind_speed DECIMAL(5,2),
    wind_deg INTEGER,
    wind_gust DECIMAL(5,2),
    clouds INTEGER,
    visibility INTEGER,
    rain_1h DECIMAL(5,2) DEFAULT 0,
    snow_1h DECIMAL(5,2) DEFAULT 0,
    
    -- Métriques qualité air
    aqi_index INTEGER,
    pm25 DECIMAL(7,2),
    pm10 DECIMAL(7,2),
    no2 DECIMAL(7,2),
    o3 DECIMAL(7,2),
    so2 DECIMAL(7,2),
    co DECIMAL(7,2),
    
    -- Métadonnées ETL (traçabilité)
    raw_weather_id BIGINT, -- Référence data lake
    raw_aqi_id BIGINT,
    
    constraint fk_fact_measures_date foreign key (capture_date) references dim_date(date_value)
);

-- Index pour optimiser les requêtes OLAP
CREATE INDEX IF NOT EXISTS idx_fact_measures_capture_date ON fact_measures(capture_date);
CREATE INDEX IF NOT EXISTS idx_fact_measures_capture_hour ON fact_measures(capture_hour);
CREATE INDEX IF NOT EXISTS idx_fact_city ON fact_measures(city_id);
CREATE INDEX IF NOT EXISTS idx_fact_weather ON fact_measures(weather_condition_id);
CREATE INDEX IF NOT EXISTS idx_fact_aqi ON fact_measures(aqi_level_id);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_index ON fact_measures(aqi_index);

COMMENT ON TABLE fact_measures IS 'Table de faits - mesures environnementales agrégées';

-- ============================================
-- INSERTION DES DONNÉES DIMENSIONS (LOOKUP TABLES)
-- ============================================

-- Pré-remplir dimension AQI avec niveaux standards
INSERT INTO dim_air_quality_level (aqi_min, aqi_max, level_name, health_concern, color_code, health_advice) VALUES
(0, 50, 'Good', 'Air quality is satisfactory', 'green', 'No health implications'),
(51, 100, 'Moderate', 'Acceptable for most people', 'yellow', 'Unusually sensitive people should consider limiting prolonged outdoor exertion'),
(101, 150, 'Unhealthy for Sensitive Groups', 'Members of sensitive groups may experience health effects', 'orange', 'Children, active adults, and people with respiratory disease should limit prolonged outdoor exertion'),
(151, 200, 'Unhealthy', 'Everyone may begin to experience health effects', 'red', 'Everyone should limit prolonged outdoor exertion'),
(201, 300, 'Very Unhealthy', 'Health alert: everyone may experience more serious health effects', 'purple', 'Everyone should avoid prolonged outdoor exertion'),
(301, 500, 'Hazardous', 'Health warnings of emergency conditions', 'maroon', 'Everyone should avoid any outdoor exertion')
ON CONFLICT DO NOTHING;

-- Pré-remplir dimension météo avec codes OpenWeather standards
INSERT INTO dim_weather_condition (weather_id, main, description, category, icon) VALUES
-- Clear
(800, 'Clear', 'clear sky', 'sunny', '01d'),
-- Clouds
(801, 'Clouds', 'few clouds', 'cloudy', '02d'),
(802, 'Clouds', 'scattered clouds', 'cloudy', '03d'),
(803, 'Clouds', 'broken clouds', 'cloudy', '04d'),
(804, 'Clouds', 'overcast clouds', 'cloudy', '04d'),
-- Rain
(500, 'Rain', 'light rain', 'rainy', '10d'),
(501, 'Rain', 'moderate rain', 'rainy', '10d'),
(502, 'Rain', 'heavy intensity rain', 'rainy', '10d'),
(503, 'Rain', 'very heavy rain', 'rainy', '10d'),
(504, 'Rain', 'extreme rain', 'rainy', '10d'),
(511, 'Rain', 'freezing rain', 'rainy', '13d'),
(520, 'Rain', 'light intensity shower rain', 'rainy', '09d'),
(521, 'Rain', 'shower rain', 'rainy', '09d'),
(522, 'Rain', 'heavy intensity shower rain', 'rainy', '09d'),
-- Drizzle
(300, 'Drizzle', 'light intensity drizzle', 'rainy', '09d'),
(301, 'Drizzle', 'drizzle', 'rainy', '09d'),
(302, 'Drizzle', 'heavy intensity drizzle', 'rainy', '09d'),
-- Thunderstorm
(200, 'Thunderstorm', 'thunderstorm with light rain', 'stormy', '11d'),
(201, 'Thunderstorm', 'thunderstorm with rain', 'stormy', '11d'),
(202, 'Thunderstorm', 'thunderstorm with heavy rain', 'stormy', '11d'),
(210, 'Thunderstorm', 'light thunderstorm', 'stormy', '11d'),
(211, 'Thunderstorm', 'thunderstorm', 'stormy', '11d'),
(212, 'Thunderstorm', 'heavy thunderstorm', 'stormy', '11d'),
-- Snow
(600, 'Snow', 'light snow', 'snowy', '13d'),
(601, 'Snow', 'snow', 'snowy', '13d'),
(602, 'Snow', 'heavy snow', 'snowy', '13d'),
-- Fog/Mist
(701, 'Mist', 'mist', 'foggy', '50d'),
(711, 'Smoke', 'smoke', 'foggy', '50d'),
(721, 'Haze', 'haze', 'foggy', '50d'),
(731, 'Dust', 'dust', 'foggy', '50d'),
(741, 'Fog', 'fog', 'foggy', '50d'),
(751, 'Sand', 'sand', 'foggy', '50d'),
(761, 'Dust', 'dust', 'foggy', '50d'),
(762, 'Ash', 'volcanic ash', 'foggy', '50d'),
(771, 'Squall', 'squalls', 'stormy', '50d'),
(781, 'Tornado', 'tornado', 'stormy', '50d')
ON CONFLICT (weather_id) DO NOTHING;

-- ============================================
-- FONCTIONS UTILITAIRES
-- ============================================

-- Fonction pour générer la dimension date (dim_date)
CREATE OR REPLACE FUNCTION populate_dim_date(start_date DATE, end_date DATE)
RETURNS void AS $$
DECLARE
    curr_date DATE := start_date;
BEGIN
    WHILE curr_date <= end_date LOOP
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
        ) VALUES (
            curr_date,
            EXTRACT(DAY FROM curr_date),
            EXTRACT(DOW FROM curr_date) + 1,
            TO_CHAR(curr_date, 'Day'),
            EXTRACT(DOY FROM curr_date),
            EXTRACT(WEEK FROM curr_date),
            CAST(TO_CHAR(curr_date, 'W') AS INTEGER),
            EXTRACT(MONTH FROM curr_date),
            TO_CHAR(curr_date, 'Month'),
            EXTRACT(QUARTER FROM curr_date),
            'Q' || EXTRACT(QUARTER FROM curr_date),
            EXTRACT(YEAR FROM curr_date),
            CASE WHEN EXTRACT(ISODOW FROM curr_date) IN (6, 7) THEN true ELSE false END,
            CASE
                WHEN EXTRACT(MONTH FROM curr_date) IN (12, 1, 2) THEN 'Winter'
                WHEN EXTRACT(MONTH FROM curr_date) IN (3, 4, 5) THEN 'Spring'
                WHEN EXTRACT(MONTH FROM curr_date) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Autumn'
            END
        ) ON CONFLICT (date_value) DO NOTHING;

        curr_date := curr_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
    current_dt TIMESTAMP WITH TIME ZONE;
    v_time_id INTEGER;
BEGIN
    current_dt := start_date::TIMESTAMP WITH TIME ZONE;
    
    WHILE current_dt <= end_date::TIMESTAMP WITH TIME ZONE + INTERVAL '23 hours' LOOP
        INSERT INTO dim_time (
            full_date, date_only, time_only, hour, day, day_name, week, month, 
            month_name, quarter, year, is_weekend, season
        ) VALUES (
            current_dt,
            current_dt::DATE,
            current_dt::TIME,
            EXTRACT(HOUR FROM current_dt)::INTEGER,
            EXTRACT(DAY FROM current_dt)::INTEGER,
            TO_CHAR(current_dt, 'Day'),
            EXTRACT(WEEK FROM current_dt)::INTEGER,
            EXTRACT(MONTH FROM current_dt)::INTEGER,
            TO_CHAR(current_dt, 'Month'),
            EXTRACT(QUARTER FROM current_dt)::INTEGER,
            EXTRACT(YEAR FROM current_dt)::INTEGER,
            EXTRACT(DOW FROM current_dt) IN (0, 6),
            CASE 
                WHEN EXTRACT(MONTH FROM current_dt) IN (12, 1, 2) THEN 'Winter'
                WHEN EXTRACT(MONTH FROM current_dt) IN (3, 4, 5) THEN 'Spring'
                WHEN EXTRACT(MONTH FROM current_dt) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Fall'
            END
        )
        ON CONFLICT (full_date) DO NOTHING;
        
        current_dt := current_dt + INTERVAL '1 hour';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour trouver le niveau AQI
CREATE OR REPLACE FUNCTION get_aqi_level_id(aqi_value INTEGER)
RETURNS INTEGER AS $$
BEGIN
    IF aqi_value IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN (
        SELECT aqi_level_id 
        FROM dim_air_quality_level 
        WHERE aqi_value BETWEEN aqi_min AND aqi_max
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_aqi_level_id IS 'Trouve le niveau AQI pour une valeur donnée';
