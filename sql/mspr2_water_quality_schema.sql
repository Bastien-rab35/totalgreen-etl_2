-- Extension pour Eau Potable et Cours d'Eau
CREATE TABLE IF NOT EXISTS dim_eau_potable_commune (
    commune_id SERIAL PRIMARY KEY,
    code_commune VARCHAR(10) UNIQUE,
    nom_commune VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_eau_potable (
    fact_id SERIAL PRIMARY KEY,
    date_value DATE REFERENCES dim_date(date_value),
    hour_of_day INTEGER,
    city_id INT REFERENCES dim_city(city_id), -- Villes du projet
    code_commune VARCHAR(10) REFERENCES dim_eau_potable_commune(code_commune),
    libelle_parametre VARCHAR(255),
    resultat_numerique DOUBLE PRECISION,
    libelle_unite VARCHAR(50),
    conclusion_conformite TEXT,
    date_prelevement TIMESTAMP WITH TIME ZONE,
    UNIQUE (code_commune, date_prelevement, libelle_parametre)
);

CREATE TABLE IF NOT EXISTS dim_cours_deau_station (
    station_id SERIAL PRIMARY KEY,
    code_station VARCHAR(50) UNIQUE,
    libelle_station VARCHAR(255),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    code_commune VARCHAR(10),
    libelle_commune VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_cours_deau_observation (
    fact_id SERIAL PRIMARY KEY,
    date_value DATE REFERENCES dim_date(date_value),
    hour_of_day INTEGER,
    station_id INT REFERENCES dim_cours_deau_station(station_id),
    libelle_parametre VARCHAR(255),
    resultat DOUBLE PRECISION,
    symbole_unite VARCHAR(50),
    code_remarque VARCHAR(50),
    date_prelevement TIMESTAMP WITH TIME ZONE,
    UNIQUE (station_id, date_prelevement, libelle_parametre)
);
