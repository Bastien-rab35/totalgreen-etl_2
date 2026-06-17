import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

db_user = "postgres"
db_password = "totalgreen-mspr35000"
db_host = "db.uqntmecpgswkdchcfwxe.supabase.co"
db_port = "5432"
db_name = "postgres"

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

query_train = """
    SELECT 
        fm.captured_at,
        dc.city_name,
        fm.temperature, 
        fm.humidity, 
        fm.wind_speed, 
        fm.aqi_index
    FROM fact_measures fm
    JOIN dim_city dc ON fm.city_id = dc.city_id
    WHERE fm.aqi_index IS NOT NULL
      AND fm.captured_at IS NOT NULL
    ORDER BY fm.captured_at
"""

df_train = pd.read_sql(query_train, engine)
df_train['datetime'] = pd.to_datetime(df_train['captured_at'])
df_train = df_train.sort_values(by=['city_name', 'datetime'])

df_train['aqi_lag_24'] = df_train.groupby('city_name')['aqi_index'].shift(24)
df_train = df_train.dropna()

df_train['mois'] = df_train['datetime'].dt.month
df_train['jour_semaine'] = df_train['datetime'].dt.dayofweek
df_train['heure'] = df_train['datetime'].dt.hour

df_train = pd.get_dummies(df_train, columns=['city_name'], drop_first=True)

features = [col for col in df_train.columns if col not in ['captured_at', 'datetime', 'aqi_index']]
X_train = df_train[features]
y_train = df_train['aqi_index']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

date_cible = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
date_cible_str = date_cible.strftime('%Y-%m-%d %H:%M:%S')

query_predict = f"""
    WITH LatestAQI AS (
        SELECT city_id, aqi_index, 
               ROW_NUMBER() OVER(PARTITION BY city_id ORDER BY captured_at DESC) as rn
        FROM fact_measures
        WHERE aqi_index IS NOT NULL
    ),
    ForecastData AS (
        SELECT fwf.forecast_id, fwf.city_id, dc.city_name, fwf.temperature, fwf.humidity, fwf.wind_speed, fwf.forecast_timestamp
        FROM fact_weather_forecast fwf
        JOIN dim_city dc ON fwf.city_id = dc.city_id
        WHERE DATE(fwf.forecast_timestamp) = DATE('{date_cible_str}')
    )
    SELECT f.forecast_id, f.city_id, f.city_name, f.temperature, f.humidity, f.wind_speed, f.forecast_timestamp, l.aqi_index as aqi_lag_24
    FROM ForecastData f
    JOIN LatestAQI l ON f.city_id = l.city_id AND l.rn = 1
"""

df_predict = pd.read_sql(query_predict, engine)

if not df_predict.empty:
    predictions_to_insert = []

    for index, row in df_predict.iterrows():
        df_city = pd.DataFrame({
            'temperature': [row['temperature']],
            'humidity': [row['humidity']],
            'wind_speed': [row['wind_speed']],
            'aqi_lag_24': [row['aqi_lag_24']],
            'mois': [row['forecast_timestamp'].month],
            'jour_semaine': [row['forecast_timestamp'].weekday()],
            'heure': [row['forecast_timestamp'].hour]
        })
        
        for col in features:
            if col not in df_city.columns:
                df_city[col] = 0
                
        col_ville = f"city_name_{row['city_name']}"
        if col_ville in df_city.columns:
            df_city[col_ville] = 1
            
        df_city = df_city[features]
        
        prediction = model.predict(df_city)[0]
        
        predictions_to_insert.append({
            'city_id': row['city_id'],
            'forecast_timestamp': row['forecast_timestamp'],
            'predicted_aqi_index': float(prediction),
            'based_on_forecast_id': row['forecast_id'],
            'model_version': 'RandomForest_v1'
        })

    if predictions_to_insert:
        df_to_insert = pd.DataFrame(predictions_to_insert)
        df_to_insert.to_sql('fact_aqi_predictions', engine, if_exists='append', index=False)