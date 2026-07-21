import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa Coroplético: Volt Mínimo por Estado")
st.markdown("Análisis de precios mínimos y densidad de tiendas por entidad federativa.")


# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
    except FileNotFoundError:
        st.error("❌ No se encontró 'datos_tiendas.csv'. Asegúrate de subirlo a GitHub.")
        return pd.DataFrame()

    # Limpiar nombres de columnas por si hay espacios
    df.columns = df.columns.str.strip()

    # Asegurar que VOLT sea numérico
    if 'VOLT' in df.columns:
        df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)

    return df


df = cargar_datos()
if df.empty:
    st.stop()

# ==========================================
# 3. PROCESAMIENTO Y MAPEO DE ESTADOS
# ==========================================
# Agrupar por estado: Volt mínimo y conteo de tiendas
df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count')
).reset_index()

# ️ CRUCIAL: Mapear tus abreviaciones a los nombres EXACTOS del GeoJSON de México
mapeo_estados = {
    'BAJA CALIFORNIA SUR': 'Baja California Sur',
    'CDMX': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACÁN': 'Michoacán de Ocampo',
    'MORELOS': 'Morelos',
    'NUEVO LEON': 'Nuevo León',
    'OAXACA': 'Oaxaca',
    'PUEBLA': 'Puebla',
    'QUERETARO': 'Querétaro',
    'SAN LUIS POTOSI': 'San Luis Potosí',
    'SAN LUIS POTOSÍ': 'San Luis Potosí',
    'SONORA': 'Sonora',
    'TABASCO': 'Tabasco',
    'TLAXCALA': 'Tlaxcala',
    'TOLUCA': 'México',
    'VALLE DE MEXICO': 'México',
    'VERACRUZ': 'Veracruz de Ignacio de la Llave'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# ==========================================
# 4. MAPA COROPLÉTICO (PLOTLY)
# ==========================================
# GeoJSON público de México (no necesitas subirlo a Git)
geojson_url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/master/mexico.json"

fig = px.choropleth(
    df_estado,
    geojson=geojson_url,
    locations='Estado_Mapa',
    color='Volt_minimo',
    featureidkey="properties.name",
    color_continuous_scale="Blues",
    range_color=(df_estado['Volt_minimo'].min(), df_estado['Volt_minimo'].max()),
    labels={'Volt_minimo': 'Volt Mínimo ($)'},
    hover_name='Estado_Mapa',
    hover_data={
        'Volt_minimo': ':$.2f',
        'Tiendas': True,
        'Estado_Mapa': False
    },
    title="Distribución de Precio Volt Mínimo por Estado"
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. TABLA DE DATOS
# ==========================================
st.subheader("📊 Resumen de Datos")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)