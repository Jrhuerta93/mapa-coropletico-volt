import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa Coroplético: Volt Mínimo por Estado")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
        df.columns = df.columns.str.strip()
        if 'VOLT' in df.columns:
            df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = cargar_datos()
if df.empty:
    st.stop()

# Procesar datos
df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count')
).reset_index()

mapeo_estados = {
    'BAJA CALIFORNIA SUR': 'Baja California Sur',
    'CDMX': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACÁN': 'Michoacán',
    'MORELOS': 'Morelos',
    'NUEVO LEON': 'Nuevo León',
    'OAXACA': 'Oaxaca',
    'PUEBLA': 'Puebla',
    'QUERETARO': 'Querétaro',
    'SAN LUIS POTOSI': 'San Luis Potosí',
    'SONORA': 'Sonora',
    'TABASCO': 'Tabasco',
    'TLAXCALA': 'Tlaxcala',
    'TOLUCA': 'México',
    'VALLE DE MEXICO': 'México',
    'VERACRUZ': 'Veracruz'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# URL CONFIABLE de GeoJSON de México (baja resolución, ~200KB)
geojson_url = "https://raw.githubusercontent.com/angelnmarrero/mexico_geojson/master/mexico_states.json"

try:
    response = requests.get(geojson_url)
    if response.status_code == 200:
        geojson_data = response.json()
        
        fig = px.choropleth(
            df_estado,
            geojson=geojson_data,
            locations='Estado_Mapa',
            color='Volt_minimo',
            featureidkey="properties.name",
            color_continuous_scale="Blues",
            labels={'Volt_minimo': 'Volt Mínimo ($)'},
            hover_data={'Volt_minimo': ':$.2f', 'Tiendas': True}
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
        
        st.plotly_chart(fig, use_container_width=True)
        st.success("✅ Mapa generado correctamente")
    else:
        st.error(f" Error al descargar GeoJSON: {response.status_code}")
        
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.info("💡 Intentando con método alternativo...")
    
    # Método alternativo: usar el built-in de Plotly
    fig = px.choropleth(
        df_estado,
        locations='Estado_Mapa',
        color='Volt_minimo',
        locationmode="country names",
        color_continuous_scale="Blues",
        scope="north america",
        labels={'Volt_minimo': 'Volt Mínimo ($)'},
        hover_data={'Volt_minimo': ':$.2f', 'Tiendas': True}
    )
    
    fig.update_layout(
        geo_scope='north america',
        geo=dict(
            center=dict(lat=23.6345, lon=-102.5528),
            projection_scale=4
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
