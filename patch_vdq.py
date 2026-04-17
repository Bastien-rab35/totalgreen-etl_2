import re

filepath = 'scripts/validate_data_quality.py'
with open(filepath, 'r') as f:
    content = f.read()

# Delete groundwater mentions
content = re.sub(r"        # 4\. Groundwater\n(?:.*?\n){1,15}", "", content)
content = content.replace(", 'groundwater_station_id'", "")

# And in limits
content = re.sub(r"        'groundwater_level_ngf_m': \(-100, 5000\),\n        'groundwater_depth_m': \(0, 1000\),\n", "", content)
content = content.replace(" 'fact_groundwater_realtime'", "")

with open(filepath, 'w') as f:
    f.write(content)
