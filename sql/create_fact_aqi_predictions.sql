CREATE TABLE IF NOT EXISTS fact_aqi_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES dim_city(city_id),
    forecast_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    predicted_aqi_index DECIMAL(10,2) NOT NULL,
    based_on_forecast_id BIGINT REFERENCES fact_weather_forecast(forecast_id),
    model_version VARCHAR(50),
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_aqi_pred_city ON fact_aqi_predictions(city_id);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_pred_forecast_ts ON fact_aqi_predictions(forecast_timestamp);

COMMENT ON TABLE fact_aqi_predictions IS 'Table de faits - prédictions ML de la qualité de l''air (AQI)';

-- RLS
ALTER TABLE fact_aqi_predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Lecture publique des prédictions" ON fact_aqi_predictions FOR SELECT USING (true);
CREATE POLICY "Insertion autorisée pour tous" ON fact_aqi_predictions FOR INSERT WITH CHECK (true);
