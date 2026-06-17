with open("src/etl_transform_to_db.py", "r") as f:
    text = f.read()
text = text.replace("'date_prelevement': f\"{full_datetime_str}Z\" if 'T' in full_datetime_str else full_datetime_str", "'date_prelevement': f\"{full_datetime_str}Z\" if full_datetime_str and 'T' in full_datetime_str else full_datetime_str")
with open("src/etl_transform_to_db.py", "w") as f:
    f.write(text)
