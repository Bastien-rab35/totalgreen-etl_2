-- ============================================
-- Insertion du référentiel des 10 villes
-- ============================================

INSERT INTO cities (id, name, latitude, longitude) VALUES
(1, 'Paris', 48.8566, 2.3522),
(2, 'Marseille', 43.2965, 5.3698),
(3, 'Lyon', 45.7640, 4.8357),
(4, 'Toulouse', 43.6047, 1.4442),
(5, 'Nice', 43.7102, 7.2620),
(6, 'Nantes', 47.2184, -1.5536),
(7, 'Montpellier', 43.6108, 3.8767),
(8, 'Strasbourg', 48.5734, 7.7521),
(9, 'Bordeaux', 44.8378, -0.5792),
(10, 'Lille', 50.6292, 3.0573)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    updated_at = CURRENT_TIMESTAMP;
