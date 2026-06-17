from src.config import config
from supabase import create_client, Client
import json

config.validate()
client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
res = client.table('raw_data_lake').select('*').eq('source', 'hubeau_cd_observations').limit(5).execute()
print(f"Items in lake: {len(res.data)}")
if res.data:
    print(json.dumps(res.data[0]['raw_data'], indent=2))
