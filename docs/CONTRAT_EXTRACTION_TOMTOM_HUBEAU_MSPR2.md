# Contrat d'extraction normalise - TomTom + Hub'Eau (MSPR2)

Ce document definit un contrat de donnees cible pour alimenter le Data Lake MSPR2.

## 1) Convention commune

- Horodatage de collecte: `horodatage_collecte_utc` en ISO 8601 UTC.
- Cle de source: `source_api` (`tomtom_flow`, `tomtom_incidents`, `hubeau_stations`, `hubeau_chroniques`, `hubeau_chroniques_tr`).
- Trace technique: `request_id`, `statut_http`, `latence_ms`.
- Payload brut conserve dans `donnees_brutes`.

## 2) Contrat TomTom Flow (par point)

```json
{
  "source_api": "tomtom_flow",
  "version_service": "4",
  "ville": "Paris",
  "code_point": "PARIS_PERIPH_NORD_01",
  "latitude": 48.9012,
  "longitude": 2.3711,
  "horodatage_collecte_utc": "2026-04-15T09:00:20Z",
  "traffic_model_id": "1234567890",
  "vitesse_actuelle_kmph": 41,
  "vitesse_fluide_kmph": 70,
  "temps_trajet_actuel_s": 153,
  "temps_trajet_fluide_s": 90,
  "indice_confiance": 0.59,
  "route_fermee": false,
  "frc": "FRC2",
  "congestion_ratio": 1.7,
  "speed_ratio": 0.586,
  "donnees_brutes": {}
}
```

## 3) Contrat TomTom Incidents (par incident)

```json
{
  "source_api": "tomtom_incidents",
  "version_service": "5",
  "ville": "Paris",
  "bbox": "2.224,48.815,2.469,48.902",
  "horodatage_collecte_utc": "2026-04-15T09:01:10Z",
  "traffic_model_id": "1234567890",
  "incident_id": "4819f7d0a15db3d9b0c3cd9203be7ba5",
  "categorie_incident": 8,
  "libelle_categorie": "RoadClosed",
  "gravite_retard": 4,
  "retard_s": 420,
  "longueur_m": 850,
  "debut_incident_utc": "2026-04-15T08:30:00Z",
  "fin_incident_utc": "2026-04-15T11:00:00Z",
  "from": "Porte Maillot",
  "to": "Porte de Clichy",
  "validite_temporelle": "present",
  "probabilite_occurrence": "certain",
  "nombre_signalements": 12,
  "score_severite_incident": 6.35,
  "geometrie": {
    "type": "LineString",
    "coordinates": []
  },
  "donnees_brutes": {}
}
```

### Formule recommandee score severite incident

`score_severite_incident = 0.5 * gravite_retard + 0.3 * ln(1 + retard_s) + 0.2 * poids_categorie`

Exemple de `poids_categorie`:

- `RoadClosed`: 5
- `Accident`: 4
- `Jam`: 3
- autres: 2

## 4) Contrat Hub'Eau Stations

```json
{
  "source_api": "hubeau_stations",
  "api_version": "1.4.1",
  "horodatage_collecte_utc": "2026-04-15T09:05:00Z",
  "bss_id": "BSS000ABC",
  "code_bss": "07548X0009/F",
  "urn_bss": "urn:ades:station:...",
  "nom_station": "Station piezo X",
  "code_commune_insee": "75056",
  "nom_commune": "Paris",
  "code_departement": "75",
  "nom_departement": "Paris",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "altitude_station_m": 35.4,
  "nb_mesures_piezo": 18520,
  "date_debut_mesure": "1998-01-01",
  "date_fin_mesure": "2026-04-14",
  "date_maj": "2026-04-15T03:10:00Z",
  "donnees_brutes": {}
}
```

## 5) Contrat Hub'Eau Chroniques (historique)

```json
{
  "source_api": "hubeau_chroniques",
  "api_version": "1.4.1",
  "horodatage_collecte_utc": "2026-04-15T09:06:00Z",
  "code_bss": "07548X0009/F",
  "date_mesure": "2026-04-14",
  "timestamp_mesure": 1713052800,
  "groundwater_level_ngf_m": 62.337,
  "groundwater_depth_m": 5.122,
  "statut_mesure": "valide",
  "qualification_mesure": "bonne",
  "mode_obtention": "mesure",
  "code_producteur": "BRGM",
  "nom_producteur": "Bureau de Recherches Geologiques et Minieres",
  "donnees_brutes": {}
}
```

## 6) Contrat Hub'Eau Chroniques TR

```json
{
  "source_api": "hubeau_chroniques_tr",
  "api_version": "1.4.1",
  "horodatage_collecte_utc": "2026-04-15T09:07:00Z",
  "bss_id": "BSS000ABC",
  "code_bss": "07548X0009/F",
  "urn_bss": "urn:ades:station:...",
  "date_mesure_utc": "2026-04-15T08:00:00Z",
  "timestamp_mesure": 1713168000,
  "date_maj_utc": "2026-04-15T08:05:00Z",
  "groundwater_level_ngf_m": 62.281,
  "groundwater_depth_m": 5.178,
  "altitude_station_m": 35.4,
  "altitude_repere_m": 67.459,
  "latitude": 48.8566,
  "longitude": 2.3522,
  "donnees_brutes": {}
}
```

## 7) Regles techniques d'implementation

- TomTom representativite: 3 a 5 points par ville minimum.
- TomTom synchronisation: reutiliser un meme `traffic_model_id` pour tous les appels d'une passe.
- TomTom quota: retry avec backoff exponentiel sur `429`.
- Hub'Eau pagination: suivre `next` jusqu'a epuisement. (Note : avec une restriction sur `date_debut_mesure` aux dernieres 24h pour les TR pour eviter l'inflation de donnees).
- Hub'Eau unites: conserver separement `groundwater_level_ngf_m` et `groundwater_depth_m`.
- Hub'Eau TR: conserver `statut`/`qualification` quand disponibles et marquer `donnee_brute=true`.

## 8) KPIs cibles dans la couche transform

- `congestion_ratio = temps_trajet_actuel_s / temps_trajet_fluide_s`
- `speed_ratio = vitesse_actuelle_kmph / vitesse_fluide_kmph`
- `incident_severity_score = somme ponderee (gravite_retard, retard_s, categorie)`
- `groundwater_trend_7d = moyenne glissante 7 jours`
- `anomaly_score = z-score glissant sur 30 jours`
