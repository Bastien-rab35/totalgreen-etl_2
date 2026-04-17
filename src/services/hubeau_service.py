import logging
import requests
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class HubeauService:
    """Service de récupération de données qualité de l'eau via Hub'Eau"""
    
    def __init__(self, eau_potable_url: str, cd_stations_url: str, cd_observations_url: str):
        self.eau_potable_url = eau_potable_url
        self.cd_stations_url = cd_stations_url
        self.cd_observations_url = cd_observations_url
        
    def _fetch_all_pages(self, url: str, params: Dict, limit_pages: int = 10) -> List[Dict]:
        """Récupère avec une limite de pages pour ne pas exploser la mémoire"""
        results = []
        current_url = url
        current_params = params.copy()
        
        pages = 0
        while current_url and pages < limit_pages:
            start_time = time.time()
            try:
                response = requests.get(current_url, params=current_params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                latence = int((time.time() - start_time) * 1000)
                
                for item in data.get('data', []):
                    item['_technical'] = {
                        "request_id": str(uuid.uuid4()),
                        "statut_http": response.status_code,
                        "latence_ms": latence
                    }
                    results.append(item)
                
                next_link = data.get('next')
                if next_link:
                    current_url = next_link
                    current_params = None
                else:
                    current_url = None
                
                pages += 1
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur requête Hub'Eau: {e}")
                break
                
        return results

    def get_eau_potable(self, nom_commune: str) -> List[Dict]:
        """Récupère les résultats qualité de l'eau potable pour une commune (dernière année en général)"""
        # On va chercher les résultats récents pour une commune donnée
        # (ex: nom_commune = 'Paris', mais attention aux arrondissements ou homonymes)
        params = {'nom_commune': nom_commune, 'date_min_prelevement': '2024-01-01', 'size': 20}
        raw_results = self._fetch_all_pages(self.eau_potable_url, params, limit_pages=1)
        
        formatted = []
        for item in raw_results:
            tech = item.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_eau_potable",
                "api_version": "v1",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "nom_commune": item.get('nom_commune'),
                "code_commune": item.get('code_commune'),
                "date_prelevement": item.get('date_prelevement'),
                "libelle_parametre": item.get('libelle_parametre'),
                "resultat_numerique": item.get('resultat_numerique'),
                "libelle_unite": item.get('libelle_unite'),
                "conclusion_conformite_prelevement": item.get('conclusion_conformite_prelevement'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": item
            })
        return formatted

    def get_cours_deau_stations(self, bbox: str) -> List[Dict]:
        """Récupère les stations de mesure de cours d'eau par bbox"""
        params = {'bbox': bbox, 'size': 100}
        raw_stations = self._fetch_all_pages(self.cd_stations_url, params, limit_pages=1)
        
        formatted = []
        for station in raw_stations:
            tech = station.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_cd_stations",
                "api_version": "v2",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "code_station": station.get('code_station'),
                "libelle_station": station.get('libelle_station'),
                "latitude": station.get('latitude'),
                "longitude": station.get('longitude'),
                "code_commune": station.get('code_commune'),
                "libelle_commune": station.get('libelle_commune'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": station
            })
        return formatted

    def get_cours_deau_observations(self, code_station: str) -> List[Dict]:
        """Récupère les observations physico-chimiques d'un cours d'eau (Limitation aux 5 dernières pages)"""
        params = {
            'code_station': code_station,
            'date_debut_prelevement': '2024-01-01',
            'size': 20,
            'sort': 'desc'
        }
        raw_obs = self._fetch_all_pages(self.cd_observations_url, params, limit_pages=1)
        
        formatted = []
        for obs in raw_obs:
            tech = obs.pop('_technical', {})
            formatted.append({
                "source_api": "hubeau_cd_observations",
                "api_version": "v2",
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "code_station": obs.get('code_station'),
                "date_prelevement": obs.get('date_prelevement'),
                "libelle_parametre": obs.get('libelle_parametre'),
                "resultat": obs.get('resultat'),
                "symbole_unite": obs.get('symbole_unite'),
                "code_remarque": obs.get('code_remarque'),
                "request_id": tech.get('request_id'),
                "statut_http": tech.get('statut_http'),
                "latence_ms": tech.get('latence_ms'),
                "donnees_brutes": obs
            })
        return formatted
