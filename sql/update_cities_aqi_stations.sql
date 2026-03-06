-- ============================================
-- Mise à jour des stations AQI pour les villes
-- ============================================
-- Ajoute le champ aqi_station et met à jour les données

-- Ajouter la colonne aqi_station si elle n'existe pas
ALTER TABLE dim_city 
ADD COLUMN IF NOT EXISTS aqi_station VARCHAR(200);

-- Si une table cities existe (référentiel), l'ajouter aussi
ALTER TABLE IF EXISTS cities 
ADD COLUMN IF NOT EXISTS aqi_station VARCHAR(200);

-- Mettre à jour les stations AQICN spécifiques pour chaque ville
UPDATE dim_city SET aqi_station = 'paris' WHERE city_name = 'Paris';
UPDATE dim_city SET aqi_station = 'marseille' WHERE city_name = 'Marseille';
UPDATE dim_city SET aqi_station = 'france/rhonealpes/rhone/lyon-centre' WHERE city_name = 'Lyon';
UPDATE dim_city SET aqi_station = 'toulouse' WHERE city_name = 'Toulouse';
UPDATE dim_city SET aqi_station = 'nice' WHERE city_name = 'Nice';
UPDATE dim_city SET aqi_station = 'nantes' WHERE city_name = 'Nantes';
UPDATE dim_city SET aqi_station = 'montpellier' WHERE city_name = 'Montpellier';
UPDATE dim_city SET aqi_station = 'strasbourg' WHERE city_name = 'Strasbourg';
UPDATE dim_city SET aqi_station = 'bordeaux' WHERE city_name = 'Bordeaux';
UPDATE dim_city SET aqi_station = 'roubaix' WHERE city_name = 'Lille';

-- Si la table cities existe, la mettre à jour également
UPDATE cities SET aqi_station = 'paris' WHERE name = 'Paris';
UPDATE cities SET aqi_station = 'marseille' WHERE name = 'Marseille';
UPDATE cities SET aqi_station = 'france/rhonealpes/rhone/lyon-centre' WHERE name = 'Lyon';
UPDATE cities SET aqi_station = 'toulouse' WHERE name = 'Toulouse';
UPDATE cities SET aqi_station = 'nice' WHERE name = 'Nice';
UPDATE cities SET aqi_station = 'nantes' WHERE name = 'Nantes';
UPDATE cities SET aqi_station = 'montpellier' WHERE name = 'Montpellier';
UPDATE cities SET aqi_station = 'strasbourg' WHERE name = 'Strasbourg';
UPDATE cities SET aqi_station = 'bordeaux' WHERE name = 'Bordeaux';
UPDATE cities SET aqi_station = 'roubaix' WHERE name = 'Lille';

-- Commentaire
COMMENT ON COLUMN dim_city.aqi_station IS 'Station AQICN spécifique pour cette ville (ex: @8613, france/rhonealpes/rhone/lyon-centre)';

SELECT 'Stations AQI mises à jour avec succès' AS result;
