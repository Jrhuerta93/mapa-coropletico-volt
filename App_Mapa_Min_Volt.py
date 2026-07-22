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
        st.error(f"❌ Error al cargar datos: {e}")
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
    'CIUDAD DE MÉXICO': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'México',
    'ESTADO DE MÉXICO': 'México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACÁN': 'Michoacán',
    'MICHOACAN': 'Michoacán',
    'MORELOS': 'Morelos',
    'NUEVO LEON': 'Nuevo León',
    'NUEVO LEÓN': 'Nuevo León',
    'OAXACA': 'Oaxaca',
    'PUEBLA': 'Puebla',
    'QUERETARO': 'Querétaro',
    'QUERÉTARO': 'Querétaro',
    'SAN LUIS POTOSI': 'San Luis Potosí',
    'SAN LUIS POTOSÍ': 'San Luis Potosí',
    'SONORA': 'Sonora',
    'TABASCO': 'Tabasco',
    'TLAXCALA': 'Tlaxcala',
    'TOLUCA': 'México',
    'VALLE DE MEXICO': 'México',
    'VERACRUZ': 'Veracruz'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# 🔑 Múltiples URLs de GeoJSON (una debe funcionar)
geojson_urls = [
    "https://raw.githubusercontent.com/CodeForPhilly/chop-data/main/mexico-states.json",
    "https://raw.githubusercontent.com/angelnmarrero/mexico_geojson/master/mexico_states.json",
    "https://raw.githubusercontent.com/codeforamerica/mexico-json/master/mexico-states.json",
    "https://gist.githubusercontent.com/Minishlink/688020/raw/9e9080f5f696f6e2f2e3e8c6f2e6f7c8f9f0f1f2/mexico.json",
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
]

geojson_data = None
url_exitosa = None

for url in geojson_urls:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            test_json = response.json()
            if 'features' in test_json:
                geojson_data = test_json
                url_exitosa = url
                st.success(f"✅ GeoJSON cargado exitosamente")
                break
    except Exception as e:
        continue

if geojson_data is None:
    st.error("❌ No se pudo cargar ningún GeoJSON de las URLs disponibles")
    st.info("💡 Mostrando solo tabla de datos")
    
    # Mostrar solo tabla si no hay GeoJSON
    st.subheader("📊 Resumen por Estado")
    df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
    df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
    df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    st.stop()

# Crear mapa
try:
    fig = px.choropleth(
        df_estado,
        geojson=geojson_data,
        locations='Estado_Mapa',
        color='Volt_minimo',
        featureidkey="properties.name",
        color_continuous_scale="Blues",
        labels={'Volt_minimo': 'Volt Mínimo ($)'},
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
    st.error(f"❌ Error al crear mapa: {e}")

# Tabla de datos
st.subheader("📊 Resumen por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
