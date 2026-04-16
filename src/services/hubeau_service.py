"""
Service Hub'Eau pour la donnée piézométrique (Nappes Phréatiques)
Stations, Historique (Chroniques) et Temps Réel (Chroniques TR)
"""
import logging
import requests
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class HubeauService:
    """Service de récupération de données d'eaux souterraines via Hub'Eau"""
    
    def __init__(self, stations_url: str, chroniques_url: str, chroniques_tr_url: str):
        self.stations_url = stations_url
        self.chroniques_url = chroniques_url
        self.chroniques_tr_url = chroniques_tr_url
        
    def _fetch_all_pages(self, url: str, params: Dict) -> List[Dict]:
        """Récupère toutes les pages en suivant l'URL 'next' (Pagination Hub'Eau)"""
        results = []
        current_url = url
        current_params = params.copy()
        
        while current_url:
            start_time = time.time()
            try:
                response = requests.get(current_url, params=current_params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                latence = int((time.time() - start_time) * 1000)
                
                for item in data.get('data', []):
                    # Stocker temporairement les métadonnées techniques pour chaque occurence
                    item['_technical'] = {
                        "request_id": str(uuid.uuid4()),
                        "statut_http": response.status_code,
                        "latence_ms": latence
                    }
                    results.append(item)
                
                # Suivre le lien 'next' si présent (qui inclus la string de query complète)
                next_link = data.get('next')
                if next_link:
                    current_url = next_link
                    current_params = None  # Plus besoin de passer les params car ils sont déjà dans l'URL next
                else:
                    current_url = None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur requête Hub'Eau: {e}")
                break
                
        return results

    def get_stations_by_bbox(self, bbox: str) -> List[Dict]:
        """
        Récupère les stations de prélèvement via une Bounding Box
        """
        params = {'bbox': bbox, 'size': 100}
        raw_stations = self._fetch_all_pages(self.stations_url, params)
        
        formatted = []
        for station in raw_stations:
            tech = station.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_stations",
                "api_version": "1.4.1",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "bss_id": station.get('bss_id'),
                "code_bss": station.get('code_bss'),
                "urn_bss": station.get('urn_bss'),
                "nom_station": station.get('nom_commune', 'Inconnu'),
                "code_commune_insee": station.get('code_commune_insee'),
                "nom_commune": station.get('nom_commune'),
                "code_departement": station.get('code_departement'),
                "nom_departement": station.get('nom_departement'),
                "latitude": station.get('y'),  # Hubeau donne y=lat et x=lon (WGS84)
                "longitude": station.get('x'),
                "altitude_station_m": station.get('altitude_station'),
                "nb_mesures_piezo": station.get('nb_mesures_piezo'),
                "date_debut_mesure": station.get('date_debut_mesure'),
                "date_fin_mesure": station.get('date_fin_mesure'),
                "date_maj": station.get('date_maj'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": station
            })
        return formatted

    def get_chroniques(self, code_bss: str) -> List[Dict]:
        """
        Récupère l'historique complet (chroniques) des niveaux pour une station.
        Utiliser prudemment en phase de bootstrap car volumineux.
        """
        params = {'code_bss': code_bss, 'size': 500}
        raw_chroniques = self._fetch_all_pages(self.chroniques_url, params)
        
        formatted = []
        for chrono in raw_chroniques:
            tech = chrono.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_chroniques",
                "api_version": "1.4.1",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "code_bss": chrono.get('code_bss'),
                "date_mesure": chrono.get('date_mesure'),
                "timestamp_mesure": chrono.get('timestamp_mesure'),
                "groundwater_level_ngf_m": chrono.get('niveau_eau_ngf'),
                "groundwater_depth_m": chrono.get('profondeur_nappe'),
                "statut_mesure": chrono.get('statut', 'inconnu'),
                "qualification_mesure": chrono.get('qualification'),
                "mode_obtention": chrono.get('mode_obtention'),
                "code_producteur": chrono.get('code_producteur'),
                "nom_producteur": chrono.get('nom_producteur'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": chrono
            })
        return formatted

    def get_chroniques_tr(self, code_bss: str) -> List[Dict]:
        """
        Récupère les niveaux d'eau Temps Réel (Chroniques TR) pour la journée en cours
        """
        params = {'code_bss': code_bss, 'size': 100, 'sort': 'desc'}
        raw_chroniques = self._fetch_all_pages(self.chroniques_tr_url, params)
        
        formatted = []
        for chrono in raw_chroniques:
            tech = chrono.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_chroniques_tr",
                "api_version": "1.4.1",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "bss_id": chrono.get('bss_id'),
                "code_bss": chrono.get('code_bss'),
                "urn_bss": chrono.get('urn_bss'),
                "date_mesure_utc": chrono.get('date_mesure'),
                "timestamp_mesure": chrono.get('timestamp_mesure'),
                "date_maj_utc": chrono.get('date_maj'),
                "groundwater_level_ngf_m": chrono.get('niveau_eaux_souterraines'),
                "groundwater_depth_m": chrono.get('profondeur_nappe'),
                "altitude_station_m": chrono.get('altitude_station'),
                "altitude_repere_m": chrono.get('altitude_repere'),
                "latitude": chrono.get('y'),
                "longitude": chrono.get('x'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": chrono
            })
        return formatted
