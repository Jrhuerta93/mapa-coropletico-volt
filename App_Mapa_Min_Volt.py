import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa Coroplético: Volt Mínimo por Estado")

@st.cache_data
def cargar_datos():
    try:
        # 🔑 IMPORTANTE: encoding='latin1' para caracteres especiales (tildes, ñ)
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
    'VERACRUZ DE IGNACIO DE LA LLAVE': 'Veracruz'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# Cargar GeoJSON local
try:
    with open('mexico.json', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    st.success(f"✅ GeoJSON cargado correctamente")
except Exception as e:
    st.error(f"❌ Error al cargar mexico.json: {e}")
    st.stop()

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
    title_text="Distribución de Precio Volt Mínimo por Estado"
)

st.plotly_chart(fig, use_container_width=True)

# Tabla de datos
st.subheader("📊 Resumen por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
