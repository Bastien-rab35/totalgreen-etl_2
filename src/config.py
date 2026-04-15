"""Configuration centralisée - Variables d'environnement"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de l'application"""
    
    # APIs
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    AQICN_API_KEY = os.getenv('AQICN_API_KEY')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Collecte
    COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 60))
    
    # URLs
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    AQICN_BASE_URL = "https://api.waqi.info/feed"
    
    @classmethod
    def validate(cls):
        """Vérifie les variables requises"""
        missing = []
        
        if not cls.OPENWEATHER_API_KEY:
            missing.append('OPENWEATHER_API_KEY')
        if not cls.AQICN_API_KEY:
            missing.append('AQICN_API_KEY')
        if not cls.SUPABASE_URL:
            missing.append('SUPABASE_URL')
        if not cls.SUPABASE_KEY:
            missing.append('SUPABASE_KEY')
            
        if missing:
            raise ValueError(f"Variables manquantes: {', '.join(missing)}")
        
        return True

config = Config()

