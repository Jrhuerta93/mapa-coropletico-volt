import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa Coroplético: Volt Mínimo por Estado")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
    df.columns = df.columns.str.strip()
    if 'VOLT' in df.columns:
        df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
    return df

df = cargar_datos()
if df.empty:
    st.stop()

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

# URLs ALTERNATIVAS (prueba en orden)
geojson_urls = [
    "https://raw.githubusercontent.com/eguidu/mexico-geojson/master/mexico-states.json",
    "https://raw.githubusercontent.com/codeforamerica/mexico-json/master/mexico-states.json",
    "https://raw.githubusercontent.com/angelnmarrero/mexico_geojson/master/mexico_states.json"
]

geojson_data = None
for url in geojson_urls:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            geojson_data = response.json()
            st.success(f"✅ GeoJSON cargado desde: {url.split('/')[2]}")
            break
    except:
        continue

if geojson_data is None:
    st.error("❌ No se pudo cargar ningún GeoJSON")
    st.stop()

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

st.subheader("📊 Resumen por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")
st.dataframe(df_tabla, use_container_width=True, hide_index=True)
