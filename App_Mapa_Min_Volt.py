import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

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
        st.error(f"Error al cargar datos: {e}")
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

# GeoJSON ligero de México (~150KB)
geojson_url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/master/mexico.json"

try:
    response = requests.get(geojson_url)
    response.raise_for_status()
    geojson_data = response.json()
    
    fig = px.choropleth(
        df_estado,
        geojson=geojson_data,
        locations='Estado_Mapa',
        color='Volt_minimo',
        featureidkey="properties.name",
        color_continuous_scale="Blues",
        range_color=(df_estado['Volt_minimo'].min(), df_estado['Volt_minimo'].max()),
        labels={'Volt_minimo': 'Volt Mínimo ($)'},
        hover_name='Estado_Mapa',
        hover_data={
            'Volt_minimo': ':$.2f',
            'Tiendas': True
        }
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0},
        title_text="Distribución de Precio Volt Mínimo por Estado"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.success("✅ Mapa generado correctamente")
    
except Exception as e:
    st.error(f"❌ Error al cargar mapa: {e}")
    st.info("💡 Verifica que el GeoJSON sea accesible")

# Tabla de datos
st.subheader("📊 Resumen por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
