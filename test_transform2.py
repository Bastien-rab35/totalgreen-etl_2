import sys
import os
import datetime
from datetime import timezone
sys.path.append(os.path.join(os.getcwd(), 'src'))
from etl_transform_to_db import TransformToDB
transformer = TransformToDB()

unprocessed_data = transformer.data_lake_service.client.table('raw_data_lake').select('*').eq('source', 'hubeau_cd_observations').limit(1).execute().data
entry = unprocessed_data[0]
raw = entry['raw_data']
date_prelevement_str = raw.get('date_prelevement')

dt = datetime.datetime.strptime(date_prelevement_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
time_info = transformer.db_service._resolve_date_and_hour(dt)
date_val, hour_val = time_info

payload = {
    'date_value': date_val,
    'hour_of_day': hour_val,
    'station_id': 1,
    'libelle_parametre': raw.get('libelle_parametre'),
    'resultat': raw.get('resultat'),
    'symbole_unite': raw.get('symbole_unite'),
    'code_remarque': raw.get('code_remarque'),
    'date_prelevement': date_prelevement_str
}
print(payload)
res = transformer.db_service.insert_fact_cours_deau_observation(payload)
print("Insert result:", res)
