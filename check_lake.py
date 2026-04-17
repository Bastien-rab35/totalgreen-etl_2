import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env')
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res_lake = client.table('raw_data_lake').select('*').eq('source', 'hubeau_chroniques_tr').limit(3).execute()
for row in res_lake.data:
    print(row['raw_data']['code_bss'] if 'code_bss' in row['raw_data'] else 'MISSING CODE_BSS', row['raw_data'])
