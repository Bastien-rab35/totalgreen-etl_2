import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'src'))
from config import config
from supabase import create_client
config.validate()
client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
res = client.table('dim_date').select('date_value').order('date_value', desc=False).limit(1).execute()
print("Min date:", res.data[0]['date_value'])
