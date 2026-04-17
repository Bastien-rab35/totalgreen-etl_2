import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env')
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res_stations = client.table('dim_groundwater_station').select('*', count='exact').execute()
print(f"Nombre de stations: {len(res_stations.data)}")
for st in res_stations.data[:5]:
    print(st)

res_gw = client.table('fact_groundwater_realtime').select('*', count='exact').execute()
print(f"\nNombre de relevés groundwater: {len(res_gw.data)}")
for gw in res_gw.data[:5]:
    print(gw)
