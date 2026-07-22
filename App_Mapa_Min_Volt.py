import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np

st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa Coroplético: Volt Mínimo por Estado")

# Ocultar mensajes de advertencia y éxito
st.set_option('deprecation.showPyplotGlobalUse', False)

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
        # Intentar descargar desde URL confiable
        try:
            url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
    return None

df = cargar_datos()
if df.empty:
    st.stop()

# Verificar si existe la columna GRUPO
if 'GRUPO' not in df.columns:
    df['GRUPO'] = df['Folio Emetrix']

# --- FILTROS ---
st.sidebar.header("🔍 Filtros")

# Crear opciones para filtros
regiones = df['REGION'].unique() if 'REGION' in df.columns else []
estados = df['ESTADO'].unique()
grupos = df['GRUPO'].unique()

# Filtros en sidebar
filtro_region = st.sidebar.selectbox(
    "Seleccionar Región",
    options=["Todas"] + sorted(regiones.tolist()) if len(regiones) > 0 else ["Todas"]
)

filtro_estado = st.sidebar.selectbox(
    "Seleccionar Estado",
    options=["Todos"] + sorted(estados.tolist())
)

filtro_grupo = st.sidebar.selectbox(
    "Seleccionar Grupo/Cliente",
    options=["Todos"] + sorted(grupos.tolist())
)

# Aplicar filtros
df_filtrado = df.copy()

if filtro_region != "Todas" and 'REGION' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['REGION'] == filtro_region]

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ESTADO'] == filtro_estado]

if filtro_grupo != "Todos":
    df_filtrado = df_filtrado[df_filtrado['GRUPO'] == filtro_grupo]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados")
    st.stop()

# Mostrar resumen de filtros
st.sidebar.markdown("---")
st.sidebar.write(f"📊 **{len(df_filtrado)}** tiendas encontradas")

# --- IDENTIFICAR LA TIENDA CON PRECIO MÍNIMO POR ESTADO ---
df_estado_min = df_filtrado.loc[df_filtrado.groupby('ESTADO')['VOLT'].idxmin()]

# Crear dataframe con los datos relevantes
df_estado = df_estado_min[['ESTADO', 'VOLT', 'GRUPO']].copy()
df_estado.columns = ['ESTADO', 'Volt_minimo', 'Grupo']

# Agregar REGION si existe
if 'REGION' in df_filtrado.columns:
    df_estado = df_estado.merge(
        df_filtrado[['ESTADO', 'REGION']].drop_duplicates('ESTADO'), 
        on='ESTADO', 
        how='left'
    )

# Contar tiendas por estado
tiendas_por_estado = df_filtrado.groupby('ESTADO').size().reset_index(name='Total_Tiendas')
df_estado = df_estado.merge(tiendas_por_estado, on='ESTADO', how='left')

# Mapeo de estados
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

# Crear texto para mostrar SOLO el precio (sin estado)
df_estado['Texto_Mapa'] = df_estado['Volt_minimo'].apply(lambda x: f"<b>${x:,.2f}</b>")

# Crear texto para hover (con toda la información)
df_estado['Hover_Texto'] = df_estado.apply(
    lambda row: f"<b>{row['Estado_Mapa']}</b><br>" +
                f"🏢 Grupo: {row['Grupo']}<br>" +
                f"💰 Precio: <b>${row['Volt_minimo']:,.2f}</b><br>" +
                f"📊 Tiendas: {row['Total_Tiendas']}",
    axis=1
)

# Cargar GeoJSON
geojson_data = cargar_geojson()
if geojson_data is None:
    st.error("❌ No se pudo cargar el archivo GeoJSON")
    st.stop()

# --- CREAR MAPA ---
st.subheader("📍 Mapa de Precios Mínimos por Estado")

# Crear figura con go.Figure
fig = go.Figure()

# 1. Agregar el mapa coropleto
fig.add_trace(go.Choropleth(
    geojson=geojson_data,
    locations=df_estado['Estado_Mapa'],
    z=df_estado['Volt_minimo'],
    featureidkey="properties.name",
    colorscale="RdYlGn_r",
    zmin=df_estado['Volt_minimo'].min(),
    zmax=df_estado['Volt_minimo'].max(),
    marker_line_width=1,
    marker_line_color='black',
    colorbar=dict(
        title="Precio Mínimo ($)",
        tickprefix="$",
        tickformat=",.0f",
        thickness=20,
        len=0.8,
        x=1.02
    ),
    hovertemplate="%{customdata[0]}<extra></extra>",
    customdata=df_estado['Hover_Texto'].values
))

# 2. Calcular centroides manualmente
def get_centroid(feature):
    try:
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
            x = sum([p[0] for p in coords]) / len(coords)
            y = sum([p[1] for p in coords]) / len(coords)
            return (x, y)
        elif feature['geometry']['type'] == 'MultiPolygon':
            all_coords = []
            for polygon in feature['geometry']['coordinates']:
                all_coords.extend(polygon[0])
            x = sum([p[0] for p in all_coords]) / len(all_coords)
            y = sum([p[1] for p in all_coords]) / len(all_coords)
            return (x, y)
    except:
        return (None, None)
    return (None, None)

centroides = {}
for feature in geojson_data['features']:
    name = feature['properties']['name']
    cent = get_centroid(feature)
    if cent[0] is not None:
        centroides[name] = cent

# Añadir coordenadas al dataframe
df_estado['lon'] = df_estado['Estado_Mapa'].map(lambda x: centroides.get(x, (None, None))[0])
df_estado['lat'] = df_estado['Estado_Mapa'].map(lambda x: centroides.get(x, (None, None))[1])

# Filtrar estados con datos
df_con_coords = df_estado.dropna(subset=['lon', 'lat'])

# 3. Agregar etiquetas de precio (SOLO PRECIO)
fig.add_trace(go.Scattergeo(
    lon=df_con_coords['lon'],
    lat=df_con_coords['lat'],
    mode='text',
    text=df_con_coords['Texto_Mapa'],
    textfont=dict(
        size=14,
        color='white',
        family='Arial, sans-serif',
        weight='bold'
    ),
    textposition='middle center',
    hoverinfo='skip',
    showlegend=False
))

# Configurar el layout
fig.update_geos(
    fitbounds="locations",
    visible=False,
    showcoastlines=True,
    coastlinecolor="black",
    showland=True,
    landcolor="lightgray",
    showocean=True,
    oceancolor="lightblue"
)

fig.update_layout(
    margin={"r":0, "t":30, "l":0, "b":0},
    height=800,
    geo=dict(
        projection_type='mercator',
        showframe=False,
        showcoastlines=True,
        coastlinecolor="black",
    ),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Arial"
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DATOS FILTRADA ---
st.subheader("📊 Datos Filtrados")

# Mostrar tabla con los datos filtrados
df_tabla = df_filtrado[['ESTADO', 'GRUPO', 'VOLT']].copy()
df_tabla.columns = ['Estado', 'Grupo', 'Precio']
df_tabla = df_tabla.sort_values(['Estado', 'Precio'])
df_tabla['Precio'] = df_tabla['Precio'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)

# --- MÉTRICAS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Precio Mínimo Global", f"${df_filtrado['VOLT'].min():,.2f}")
with col2:
    st.metric("📈 Precio Máximo Global", f"${df_filtrado['VOLT'].max():,.2f}")
with col3:
    st.metric("📊 Precio Promedio", f"${df_filtrado['VOLT'].mean():,.2f}")

# --- EXPORTAR DATOS ---
st.subheader("📥 Descargar Datos Filtrados")

csv = df_tabla.to_csv(index=False)
st.download_button(
    label="📥 Descargar datos filtrados (CSV)",
    data=csv,
    file_name="datos_filtrados.csv",
    mime="text/csv"
)
