from src.config import config
from src.services.tomtom_service import TomTomService
config.validate()
ts = TomTomService(config.TOMTOM_API_KEY, config.TOMTOM_FLOW_BASE_URL, config.TOMTOM_INCIDENTS_BASE_URL)
res = ts.get_traffic_incidents("Paris", "2.25,48.75,2.45,48.95", "test")
print(len(res))
