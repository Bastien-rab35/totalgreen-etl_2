#!/usr/bin/env python3
"""
GoodAir Dashboard - Tableau de Bord Interactif
Visualisation des données de qualité de l'air et météorologie
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client

# Configuration Streamlit
st.set_page_config(
    page_title="GoodAir Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()

# ========== CONNEXION BASE DE DONNÉES ==========
@st.cache_resource
def get_supabase_client():
    """Connexion Supabase"""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

# ========== CHARGEMENT DONNÉES ==========
@st.cache_data(ttl=3600)
def load_data(hours=24):
    """Charge les données des dernières X heures"""
    supabase = get_supabase_client()
    
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    response = supabase.table('fact_measures') \
        .select('*') \
        .gte('captured_at', cutoff_time) \
        .order('captured_at', desc=True) \
        .execute()
    
    df = pd.DataFrame(response.data)
    if len(df) > 0:
        df['captured_at'] = pd.to_datetime(df['captured_at'])
    
    return df

@st.cache_data(ttl=3600)
def load_cities():
    """Liste des villes disponibles"""
    supabase = get_supabase_client()
    response = supabase.table('dim_city').select('city_id, city_name').execute()
    return pd.DataFrame(response.data)

# ========== STYLE ET TITRE ==========
st.markdown("""
<style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
    }
    .alert-danger {
        padding: 10px;
        border-left: 5px solid #ff6b6b;
        background-color: #ffe0e0;
        border-radius: 5px;
        margin: 10px 0;
    }
    .alert-warning {
        padding: 10px;
        border-left: 5px solid #ffa94d;
        background-color: #ffe8cc;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌍 GoodAir - Tableau de Bord</div>', unsafe_allow_html=True)
st.markdown("**Qualité de l'air et conditions météorologiques en France**")

# ========== SIDEBAR - FILTRES ==========
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    hours_filter = st.slider(
        "Période à analyser (heures)",
        1, 168, 24
    )
    
    cities_df = load_cities()
    selected_cities = st.multiselect(
        "Villes",
        cities_df['city_name'].unique(),
        default=cities_df['city_name'].unique()[:3]
    )
    
    st.divider()
    st.markdown("### Seuils d'alerte")
    aqi_threshold = st.slider("AQI critique", 100, 500, 300)
    pm25_threshold = st.slider("PM2.5 (µg/m³)", 50, 500, 150)
    
    st.divider()
    if st.button("🔄 Rafraîchir les données"):
        st.cache_data.clear()
        st.rerun()

# ========== CHARGEMENT ET FILTRAGE ==========
try:
    df = load_data(hours=hours_filter)
    
    if len(df) == 0:
        st.warning("⚠️ Aucune donnée disponible pour cette période")
        st.stop()
    
    # Filtrer par villes sélectionnées
    df = df[df['city_name'].isin(selected_cities)]
    
    if len(df) == 0:
        st.warning("⚠️ Aucune donnée pour les villes sélectionnées")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Erreur de connexion: {e}")
    st.stop()

# ========== KPI PRINCIPAUX ==========
st.subheader("📊 Indicateurs Clés de Performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    aqi_mean = df['aqi'].mean()
    st.metric(
        "AQI Moyen",
        f"{aqi_mean:.0f}",
        delta=f"Seuil critique: {aqi_threshold}"
    )

with col2:
    temp_mean = df['temperature'].mean()
    st.metric(
        "Température Moyenne",
        f"{temp_mean:.1f}°C",
        delta=f"Min: {df['temperature'].min():.1f}°C"
    )

with col3:
    pm25_mean = df['pm2_5'].mean()
    st.metric(
        "PM2.5 Moyen",
        f"{pm25_mean:.1f} µg/m³",
        delta=f"Seuil alerte: {pm25_threshold}"
    )

with col4:
    humidity_mean = df['humidity'].mean()
    st.metric(
        "Humidité Moyenne",
        f"{humidity_mean:.0f}%",
        delta=f"Max: {df['humidity'].max():.0f}%"
    )

# ========== ALERTES ==========
st.subheader("⚠️ Alertes Détectées")

alerts = []

# Alerte AQI
df_alert_aqi = df[df['aqi'] > aqi_threshold]
if len(df_alert_aqi) > 0:
    st.markdown(f"""
    <div class="alert-danger">
    <strong>🔴 AQI Critique:</strong> {len(df_alert_aqi)} mesures au-dessus de {aqi_threshold}
    </div>
    """, unsafe_allow_html=True)

# Alerte PM2.5
df_alert_pm25 = df[df['pm2_5'] > pm25_threshold]
if len(df_alert_pm25) > 0:
    st.markdown(f"""
    <div class="alert-warning">
    <strong>🟠 PM2.5 Élevé:</strong> {len(df_alert_pm25)} mesures au-dessus de {pm25_threshold} µg/m³
    </div>
    """, unsafe_allow_html=True)

if len(df_alert_aqi) == 0 and len(df_alert_pm25) == 0:
    st.info("✅ Aucune alerte détectée - Qualité de l'air satisfaisante")

# ========== GRAPHIQUES ==========
st.subheader("📈 Évolution Temporelle")

# Graphique 1: Evolution AQI par ville
fig_aqi = px.line(
    df.sort_values('captured_at'),
    x='captured_at',
    y='aqi',
    color='city_name',
    title='Évolution de l\'AQI par ville',
    labels={'aqi': 'AQI', 'captured_at': 'Date/Heure', 'city_name': 'Ville'}
)
fig_aqi.add_hline(y=aqi_threshold, line_dash="dash", line_color="red", annotation_text="Seuil critique")
st.plotly_chart(fig_aqi, use_container_width=True)

# Graphique 2: Température vs AQI (scatter)
fig_scatter = px.scatter(
    df,
    x='temperature',
    y='aqi',
    color='city_name',
    size='pm2_5',
    title='Corrélation: Température vs AQI (taille = PM2.5)',
    labels={'temperature': 'Température (°C)', 'aqi': 'AQI', 'city_name': 'Ville'},
    hover_data=['humidity', 'pressure']
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Graphique 3: Distribution PM2.5
fig_pm25 = px.box(
    df,
    x='city_name',
    y='pm2_5',
    title='Distribution des PM2.5 par ville',
    labels={'pm2_5': 'PM2.5 (µg/m³)', 'city_name': 'Ville'}
)
fig_pm25.add_hline(y=pm25_threshold, line_dash="dash", line_color="orange", annotation_text="Seuil alerte")
st.plotly_chart(fig_pm25, use_container_width=True)

# ========== TABLEAU DE DONNÉES ==========
st.subheader("📋 Données Détaillées")

# Agrégation par ville
agg_data = df.groupby('city_name').agg({
    'aqi': ['mean', 'max', 'min'],
    'temperature': 'mean',
    'pm2_5': 'mean',
    'pm10': 'mean',
    'humidity': 'mean'
}).round(2)

agg_data.columns = ['AQI Moy', 'AQI Max', 'AQI Min', 'Temp (°C)', 'PM2.5', 'PM10', 'Humidité (%)']

st.dataframe(agg_data, use_container_width=True)

# ========== HEATMAP CORRÉLATIONS ==========
st.subheader("🔗 Matrice de Corrélation")

correlation_cols = ['temperature', 'humidity', 'pressure', 'aqi', 'pm2_5', 'pm10']
corr_matrix = df[correlation_cols].corr()

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=corr_matrix.values,
        x=correlation_cols,
        y=correlation_cols,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10}
    )
)
fig_heatmap.update_layout(title="Corrélations entre Variables", width=800, height=700)
st.plotly_chart(fig_heatmap, use_container_width=True)

# ========== STATISTIQUES DÉTAILLÉES ==========
st.subheader("📊 Statistiques Détaillées")

tab1, tab2, tab3 = st.tabs(["Qualité de l'air", "Météo", "Télécharger"])

with tab1:
    st.write("**Paramètres de qualité de l'air**")
    aqi_stats = pd.DataFrame({
        'Métrique': ['AQI', 'PM2.5', 'PM10', 'NO2', 'O3', 'SO2', 'CO'],
        'Moyen': [
            f"{df['aqi'].mean():.0f}",
            f"{df['pm2_5'].mean():.1f}",
            f"{df['pm10'].mean():.1f}",
            f"{df['no2'].mean():.1f}",
            f"{df['o3'].mean():.1f}",
            f"{df['so2'].mean():.1f}",
            f"{df['co'].mean():.0f}"
        ],
        'Max': [
            f"{df['aqi'].max():.0f}",
            f"{df['pm2_5'].max():.1f}",
            f"{df['pm10'].max():.1f}",
            f"{df['no2'].max():.1f}",
            f"{df['o3'].max():.1f}",
            f"{df['so2'].max():.1f}",
            f"{df['co'].max():.0f}"
        ]
    })
    st.dataframe(aqi_stats, use_container_width=True, hide_index=True)

with tab2:
    st.write("**Paramètres météorologiques**")
    weather_stats = pd.DataFrame({
        'Paramètre': ['Température', 'Humidité', 'Pression', 'Visibilité', 'Vitesse vent'],
        'Moyen': [
            f"{df['temperature'].mean():.1f}°C",
            f"{df['humidity'].mean():.0f}%",
            f"{df['pressure'].mean():.0f} hPa",
            f"{df['visibility'].mean():.0f} m",
            f"{df['wind_speed'].mean():.1f} m/s"
        ],
        'Min/Max': [
            f"{df['temperature'].min():.1f}°C / {df['temperature'].max():.1f}°C",
            f"{df['humidity'].min():.0f}% / {df['humidity'].max():.0f}%",
            f"{df['pressure'].min():.0f} / {df['pressure'].max():.0f} hPa",
            f"{df['visibility'].min():.0f} / {df['visibility'].max():.0f} m",
            f"{df['wind_speed'].min():.1f} / {df['wind_speed'].max():.1f} m/s"
        ]
    })
    st.dataframe(weather_stats, use_container_width=True, hide_index=True)

with tab3:
    st.write("**Télécharger les données**")
    
    # CSV
    csv = df.sort_values('captured_at').to_csv(index=False)
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name=f"goodair_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Excel
    try:
        import openpyxl
        buffer = pd.ExcelWriter(f"/tmp/goodair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", engine='openpyxl')
        df.to_excel(buffer, sheet_name='Mesures', index=False)
        buffer.close()
        
        with open(buffer.path, 'rb') as f:
            st.download_button(
                label="📊 Télécharger en Excel",
                data=f.read(),
                file_name=f"goodair_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
    except:
        pass

# ========== FOOTER ==========
st.divider()
st.markdown("""
<div style='text-align: center; color: grey; font-size: 12px;'>
    🌍 GoodAir - Laboratoire de Recherche TotalGreen  
    Dernière mise à jour: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """  
    📧 Contact: research@goodair.fr
</div>
""", unsafe_allow_html=True)
