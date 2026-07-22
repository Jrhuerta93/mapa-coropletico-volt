import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np

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

# Verificar si existe la columna GRUPO
if 'GRUPO' not in df.columns:
    st.warning("⚠️ No se encontró la columna 'GRUPO'. Usando 'Folio Emetrix' como alternativa.")
    df['GRUPO'] = df['Folio Emetrix']

# --- IDENTIFICAR LA TIENDA CON PRECIO MÍNIMO POR ESTADO ---
# Primero, encontrar el precio mínimo por estado
df_estado_min = df.loc[df.groupby('ESTADO')['VOLT'].idxmin()]

# Crear dataframe con los datos relevantes
df_estado = df_estado_min[['ESTADO', 'VOLT', 'GRUPO']].copy()
df_estado.columns = ['ESTADO', 'Volt_minimo', 'Grupo']

# Contar tiendas por estado para mostrar en hover
tiendas_por_estado = df.groupby('ESTADO').size().reset_index(name='Total_Tiendas')
df_estado = df_estado.merge(tiendas_por_estado, on='ESTADO', how='left')

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

# Crear columna para formato de moneda
df_estado['Volt_minimo_formato'] = df_estado['Volt_minimo'].apply(lambda x: f"${x:,.2f}")

# Crear texto para mostrar en el mapa (formato HTML)
df_estado['Texto_Mapa'] = df_estado.apply(
    lambda row: f"<b>{row['Estado_Mapa']}</b><br>{row['Grupo']}<br><b>${row['Volt_minimo']:,.2f}</b>", 
    axis=1
)

# Cargar GeoJSON
geojson_data = cargar_geojson()
if geojson_data is None:
    st.error("❌ No se pudo cargar el archivo GeoJSON. Verifica tu conexión a internet o el archivo local.")
    st.stop()

st.success(f"✅ GeoJSON cargado correctamente")

# Verificar estados faltantes
try:
    nombres_geojson = [feature['properties']['name'] for feature in geojson_data['features']]
    estados_faltantes = set(df_estado['Estado_Mapa'].dropna()) - set(nombres_geojson)
    if estados_faltantes:
        st.warning(f"⚠️ Estados que no se encontraron en el mapa: {', '.join(estados_faltantes)}")
except Exception as e:
    st.warning(f"⚠️ No se pudieron verificar los nombres de estados: {e}")

# --- CREAR MAPA CON GO (para mejor control de etiquetas) ---
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
    hovertemplate="<b>%{location}</b><br>" +
                  "🏢 Grupo: <b>%{customdata[0]}</b><br>" +
                  "💰 Precio: <b>$%{z:,.2f}</b><br>" +
                  "📊 Tiendas: %{customdata[1]}<br>" +
                  "<extra></extra>",
    customdata=df_estado[['Grupo', 'Total_Tiendas']].values
))

# 2. Agregar etiquetas de texto en el mapa
# Calcular centroides manualmente
def get_centroid(feature):
    """Calcular centroide de un polígono"""
    try:
        # Para polígonos simples
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
            x = sum([p[0] for p in coords]) / len(coords)
            y = sum([p[1] for p in coords]) / len(coords)
            return (x, y)
        # Para multipolígonos
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

# Crear diccionario de centroides
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

# Agregar scatter para etiquetas
fig.add_trace(go.Scattergeo(
    lon=df_con_coords['lon'],
    lat=df_con_coords['lat'],
    mode='text',
    text=df_con_coords['Texto_Mapa'],
    textfont=dict(
        size=10,
        color='black',
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

# --- SECCIÓN DE ANÁLISIS ---
st.subheader("📊 Análisis de Precios Mínimos")

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    precio_min = df_estado['Volt_minimo'].min()
    estado_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Estado_Mapa'].iloc[0]
    grupo_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Grupo'].iloc[0]
    st.metric("💰 Precio más bajo", f"${precio_min:,.2f}", f"{estado_min} - {grupo_min}")
    
with col2:
    precio_max = df_estado['Volt_minimo'].max()
    estado_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Estado_Mapa'].iloc[0]
    grupo_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Grupo'].iloc[0]
    st.metric("💸 Precio más alto", f"${precio_max:,.2f}", f"{estado_max} - {grupo_max}")
    
with col3:
    precio_prom = df_estado['Volt_minimo'].mean()
    st.metric("📊 Precio promedio", f"${precio_prom:,.2f}")
    
with col4:
    st.metric("🏪 Estados con datos", len(df_estado))

# --- TABLA CON GRUPO Y PRECIO ---
st.subheader("📋 Tabla de Precios Mínimos por Estado")

# Crear tabla con formato mejorado
df_tabla = df_estado[['Estado_Mapa', 'Grupo', 'Volt_minimo', 'Total_Tiendas']].copy()
df_tabla.columns = ['Estado', 'Grupo con precio mínimo', 'Precio Mínimo', 'Total Tiendas']
df_tabla = df_tabla.sort_values(by='Precio Mínimo', ascending=True)

# Formatear precios
df_tabla['Precio Mínimo'] = df_tabla['Precio Mínimo'].apply(lambda x: f"${x:,.2f}")

# Resaltar los precios más bajos y altos
def resaltar_precios(row):
    precio_limpio = float(row['Precio Mínimo'].replace('$', '').replace(',', ''))
    if precio_limpio == df_estado['Volt_minimo'].min():
        return ['background-color: #90EE90'] * len(row)
    elif precio_limpio == df_estado['Volt_minimo'].max():
        return ['background-color: #FFB6C1'] * len(row)
    return [''] * len(row)

styled_df = df_tabla.style.apply(resaltar_precios, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- GRÁFICO DE BARRAS ---
st.subheader("📈 Distribución de Precios Mínimos por Estado")

fig_bar = px.bar(
    df_tabla.sort_values(by='Precio Mínimo', ascending=False),
    x='Estado',
    y=df_tabla['Precio Mínimo'].str.replace('$', '').str.replace(',', '').astype(float),
    color='Precio Mínimo',
    color_continuous_scale='RdYlGn_r',
    title="Precios Mínimos por Estado (Ordenados de Mayor a Menor)",
    labels={'y': 'Precio Mínimo ($)', 'x': 'Estado'},
    text=df_tabla['Grupo con precio mínimo']
)

fig_bar.update_traces(
    textposition='outside',
    textfont=dict(size=9)
)

fig_bar.update_layout(
    xaxis_tickangle=-45,
    height=500,
    showlegend=False,
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

st.plotly_chart(fig_bar, use_container_width=True)

# --- EXPORTAR DATOS ---
st.subheader("📥 Descargar Datos")

csv_min = df_tabla.to_csv(index=False)
st.download_button(
    label="📥 Descargar precios mínimos (CSV)",
    data=csv_min,
    file_name="precios_minimos_por_estado.csv",
    mime="text/csv"
)

# Mostrar estados sin datos
estados_sin_datos = set(nombres_geojson) - set(df_estado['Estado_Mapa'].dropna())
if estados_sin_datos:
    st.info(f"ℹ️ Estados sin datos en el mapa: {', '.join(sorted(estados_sin_datos))}")
