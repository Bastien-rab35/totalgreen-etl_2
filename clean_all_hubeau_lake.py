import logging
from src.config import config
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean():
    config.validate()
    client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    # On liste toutes les sources probables de hubeau
    sources = ['hubeau_eau_potable', 'hubeau_cd_stations', 'hubeau_cd_observations', 'hubeau_stations', 'hubeau_nappes']
    
    for src in sources:
        res = client.table('raw_data_lake').select('id', count='exact').eq('source', src).limit(1).execute()
        total = res.count if res.count else 0
        logger.info(f"Source: {src} - Lignes trouvées : {total}")
        
        if total == 0:
            continue
            
        deleted = 0
        while True:
            res = client.table('raw_data_lake').select('id').eq('source', src).limit(500).execute()
            if not res.data:
                break
            
            ids = [r['id'] for r in res.data]
            del_res = client.table('raw_data_lake').delete().in_('id', ids).execute()
            count = len(del_res.data) if del_res.data else 0
            deleted += count
            logger.info(f"Suppression {count} lignes de {src} - Total en cours : {deleted}")
            
        logger.info(f"Terminé pour {src}. Supprimées : {deleted}")

if __name__ == "__main__":
    clean()
