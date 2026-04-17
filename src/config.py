import os
import logging
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()

def setup_logging(level: int = logging.INFO) -> None:
    """Configuration centralisée du logging pour tout le projet."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Réduire le bruit de certains modules très prolixes
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

@dataclass
class Config:
    """Configuration centralisée de l'application (Singleton-like behavior)."""
    
    # APIs
    OPENWEATHER_API_KEY: str = os.getenv('OPENWEATHER_API_KEY', '')
    AQICN_API_KEY: str = os.getenv('AQICN_API_KEY', '')
    TOMTOM_API_KEY: str = os.getenv('TOMTOM_API_KEY', '')
    
    # Supabase
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    
    # Collecte
    COLLECTION_INTERVAL: int = int(os.getenv('COLLECTION_INTERVAL', 60))
    
    # URLs de base
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    AQICN_BASE_URL: str = "https://api.waqi.info/feed"
    TOMTOM_FLOW_BASE_URL: str = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    TOMTOM_INCIDENTS_BASE_URL: str = "https://api.tomtom.com/traffic/services/5/incidentDetails"
    HUBEAU_EAU_POTABLE_URL: str = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
    HUBEAU_CD_STATIONS_URL: str = "https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/station_pc"
    HUBEAU_CD_OBSERVATIONS_URL: str = "https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/analyse_pc"

    def validate(self) -> bool:
        """Vérifie la présence absolue des variables d'environnement requises."""
        missing: List[str] = []
        
        if not self.OPENWEATHER_API_KEY: missing.append('OPENWEATHER_API_KEY')
        if not self.AQICN_API_KEY: missing.append('AQICN_API_KEY')
        if not self.TOMTOM_API_KEY: missing.append('TOMTOM_API_KEY')
        if not self.SUPABASE_URL: missing.append('SUPABASE_URL')
        if not self.SUPABASE_KEY: missing.append('SUPABASE_KEY')
            
        if missing:
            raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")
        
        return True

# Instance globale à utiliser dans tous les autres modules
config = Config()

