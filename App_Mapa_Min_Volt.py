import streamlit as st
import pandas as pd
import plotly.express as px
import json
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
        st.error(f"❌ Error al cargar datos: {e}")
        return pd.DataFrame()

@st.cache_data
def cargar_geojson():
    # Intentar cargar desde archivo local primero
    try:
        with open('mexico.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar archivo local: {e}")
        
        # Intentar descargar desde URL confiable
        try:
            url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error descargando GeoJSON: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error descargando GeoJSON: {e}")
    
    return None

df = cargar_datos()
if df.empty:
    st.stop()

# Procesar datos
df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count')
).reset_index()

# Mapeo de estados (incluye variaciones con tildes)
mapeo_estados = {
    'BAJA CALIFORNIA SUR': 'Baja California Sur',
    'CDMX': 'Ciudad de México',
    'CIUDAD DE MEXICO': 'Ciudad de México',
    'CIUDAD DE MÉXICO': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'México',
    'ESTADO DE MEXICO': 'México',
    'ESTADO DE MÉXICO': 'México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACAN': 'Michoacán',
    'MICHOACÁN': 'Michoacán',
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
    'VALLE DE MÉXICO': 'México',
    'VERACRUZ': 'Veracruz',
    'VERACRUZ DE IGNACIO DE LA LLAVE': 'Veracruz',
    'BAJA CALIFORNIA': 'Baja California',
    'CAMPECHE': 'Campeche',
    'COAHUILA': 'Coahuila de Zaragoza',
    'COLIMA': 'Colima',
    'DURANGO': 'Durango',
    'GUERRERO': 'Guerrero',
    'NAYARIT': 'Nayarit',
    'QUINTANA ROO': 'Quintana Roo',
    'SINALOA': 'Sinaloa',
    'TAMAULIPAS': 'Tamaulipas',
    'YUCATAN': 'Yucatán',
    'ZACATECAS': 'Zacatecas'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# Cargar GeoJSON
geojson_data = cargar_geojson()
if geojson_data is None:
    st.error("❌ No se pudo cargar el archivo GeoJSON. Verifica tu conexión a internet o el archivo local.")
    st.stop()

st.success(f"✅ GeoJSON cargado correctamente")

# Verificar estados faltantes
estados_faltantes = set(df_estado['Estado_Mapa'].dropna()) - set([feature['properties']['name'] for feature in geojson_data['features']])
if estados_faltantes:
    st.warning(f"⚠️ Estados que no se encontraron en el mapa: {', '.join(estados_faltantes)}")

# Crear mapa
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
    title_text="Distribución de Precio Volt Mínimo por Estado",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# Tabla de datos
st.subheader("📊 Resumen por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

# Mostrar estado con datos vs sin datos
col1, col2 = st.columns(2)
with col1:
    st.metric("Total de Estados con datos", len(df_tabla))
with col2:
    st.metric("Precio más bajo", df_tabla['Volt Mínimo'].min())

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
