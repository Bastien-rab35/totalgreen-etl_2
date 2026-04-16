"""
Service d'extraction de données trafic depuis TomTom API
(Flow & Incidents)
"""
import logging
import requests
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TomTomService:
    """Service de récupération du Trafic Routier via TomTom"""
    
    def __init__(self, api_key: str, flow_base_url: str, incidents_base_url: str):
        self.api_key = api_key
        self.flow_base_url = flow_base_url
        self.incidents_base_url = incidents_base_url
        self.max_retries = 3

    def _request_with_backoff(self, url: str, params: Dict) -> Optional[Dict]:
        """Exécute une requête avec un mécanisme de retry / exponential backoff (quota 429)"""
        params['key'] = self.api_key
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                
                # Gestion quota TomTom
                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Quota TomTom dépassé (429), retry en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur API TomTom ({url}): {e}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)
                
        return None

    def get_traffic_flow(self, code_point: str, city: str, lat: float, lon: float, traffic_model_id: str) -> Optional[Dict]:
        """
        Récupère l'état du flux du trafic (vitesse) pour un point précis.
        """
        start_time = time.time()
        
        params = {
            'point': f"{lat},{lon}"
        }
        
        raw_data = self._request_with_backoff(self.flow_base_url, params)
        latence_ms = int((time.time() - start_time) * 1000)
        
        if not raw_data or 'flowSegmentData' not in raw_data:
            return None
            
        flow_data = raw_data['flowSegmentData']
        
        # KPIS (Ratios calculés on the fly)
        current_time = flow_data.get('currentTravelTime')
        free_time = flow_data.get('freeFlowTravelTime')
        congestion = (current_time / free_time) if current_time and free_time else None
        
        current_speed = flow_data.get('currentSpeed')
        free_speed = flow_data.get('freeFlowSpeed')
        speed_rat = (current_speed / free_speed) if current_speed and free_speed else None
        
        return {
            "source_api": "tomtom_flow",
            "version_service": "4",
            "ville": city,
            "code_point": code_point,
            "latitude": lat,
            "longitude": lon,
            "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
            "traffic_model_id": traffic_model_id,
            "vitesse_actuelle_kmph": current_speed,
            "vitesse_fluide_kmph": free_speed,
            "temps_trajet_actuel_s": current_time,
            "temps_trajet_fluide_s": free_time,
            "indice_confiance": flow_data.get('confidence'),
            "route_fermee": flow_data.get('roadClosure', False),
            "frc": flow_data.get('frc'),
            "congestion_ratio": congestion,
            "speed_ratio": speed_rat,
            "request_id": str(uuid.uuid4()),
            "statut_http": 200 if raw_data else 500,
            "latence_ms": latence_ms,
            "donnees_brutes": raw_data
        }

    def get_traffic_incidents(self, city: str, bbox: str, traffic_model_id: str) -> List[Dict]:
        """
        Récupère les incidents en cours sur une Bounding Box (bbox).
        """
        start_time = time.time()
        
        # fields structure per tomtom documentation for incidents layer
        params = {
            'bbox': bbox,
            'fields': '{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code,iconCategory},startTime,endTime,from,to,length,delay,roadNumbers,timeValidity,probabilityOfOccurrence,numberOfReports}}}',
            'language': 'fr-FR'
        }
        
        raw_data = self._request_with_backoff(self.incidents_base_url, params)
        latence_ms = int((time.time() - start_time) * 1000)
        
        incidents_list = []
        if not raw_data or 'incidents' not in raw_data:
            return incidents_list
            
        for inc in raw_data['incidents']:
            props = inc.get('properties', {})
            geom = inc.get('geometry', {})
            
            incident_data = {
                "source_api": "tomtom_incidents",
                "version_service": "5",
                "ville": city,
                "bbox": bbox,
                "horodatage_collecte_utc": datetime.now(timezone.utc).isoformat(),
                "traffic_model_id": traffic_model_id,
                "incident_id": props.get('id'),
                "categorie_incident": props.get('iconCategory'),
                "libelle_categorie": "Unknown",  # Mapped later in DWH
                "gravite_retard": props.get('magnitudeOfDelay'),
                "retard_s": props.get('delay', 0),
                "longueur_m": props.get('length', 0),
                "debut_incident_utc": props.get('startTime'),
                "fin_incident_utc": props.get('endTime'),
                "from": props.get('from'),
                "to": props.get('to'),
                "validite_temporelle": props.get('timeValidity'),
                "probabilite_occurrence": props.get('probabilityOfOccurrence'),
                "nombre_signalements": props.get('numberOfReports', 0),
                "request_id": str(uuid.uuid4()),
                "statut_http": 200,
                "latence_ms": latence_ms,
                "geometrie": geom,
                "donnees_brutes": inc
            }
            incidents_list.append(incident_data)
            
        return incidents_list
