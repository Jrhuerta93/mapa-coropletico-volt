import streamlit as st
import pandas as pd
import plotly.express as px
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

# --- IDENTIFICAR LA TIENDA CON PRECIO MÍNIMO POR ESTADO ---
# Primero, encontrar el precio mínimo por estado
df_estado_min = df.loc[df.groupby('ESTADO')['VOLT'].idxmin()]

# Crear dataframe con los datos relevantes
df_estado = df_estado_min[['ESTADO', 'VOLT', 'Folio Emetrix']].copy()
df_estado.columns = ['ESTADO', 'Volt_minimo', 'Cliente']

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

# Crear columna para formato de moneda en hover
df_estado['Volt_minimo_formato'] = df_estado['Volt_minimo'].apply(lambda x: f"${x:,.2f}")

# Crear texto para mostrar en el mapa (para usar con texttemplate)
df_estado['Texto_Mapa'] = df_estado.apply(
    lambda row: f"<b>{row['Estado_Mapa']}</b><br>{row['Cliente']}<br>${row['Volt_minimo']:,.2f}", 
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

# --- MAPA CON NOMBRE DE CLIENTE Y PRECIO ---
st.subheader("📍 Mapa de Precios Mínimos por Estado")

# Crear mapa con mejor visualización
fig = px.choropleth(
    df_estado,
    geojson=geojson_data,
    locations='Estado_Mapa',
    color='Volt_minimo',
    featureidkey="properties.name",
    color_continuous_scale="RdYlGn_r",  # Rojo = caro, Verde = barato (invertido)
    range_color=[df_estado['Volt_minimo'].min(), df_estado['Volt_minimo'].max()],
    labels={'Volt_minimo': 'Precio Mínimo ($)'},
    hover_data={
        'Estado_Mapa': True,
        'Cliente': True,
        'Volt_minimo': True,
        'Volt_minimo_formato': True,
        'Total_Tiendas': True
    },
    template='plotly_white'
)

# Personalizar hover con información completa
fig.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>" +
                  "🏪 Cliente: <b>%{customdata[1]}</b><br>" +
                  "💰 Precio Mínimo: <b>$%{customdata[2]:,.2f}</b><br>" +
                  "📊 Total Tiendas: %{customdata[4]}<br>" +
                  "<extra></extra>",
    customdata=df_estado[['Estado_Mapa', 'Cliente', 'Volt_minimo', 'Volt_minimo_formato', 'Total_Tiendas']].values,
    # Agregar etiquetas en el mapa con el nombre del cliente y precio
    text=df_estado['Texto_Mapa'],
    texttemplate='%{text}',
    textposition='middle center',
    textfont=dict(
        size=9,
        color='black',
        family='Arial, sans-serif'
    ),
    textangle=0
)

# Ajustar geografía
fig.update_geos(
    fitbounds="locations", 
    visible=False,
    showcoastlines=True,
    coastlinecolor="black",
    showland=True,
    landcolor="lightgray"
)

# Mejorar layout
fig.update_layout(
    margin={"r":0, "t":30, "l":0, "b":0},
    height=700,
    coloraxis_colorbar=dict(
        title="Precio Mínimo ($)",
        tickprefix="$",
        tickformat=",.0f",
        thickness=25,
        len=0.8,
        x=1.02
    ),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Arial"
    ),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        projection_type='mercator'
    )
)

# Mostrar el mapa
st.plotly_chart(fig, use_container_width=True)

# --- SECCIÓN DE ANÁLISIS ---
st.subheader("📊 Análisis de Precios Mínimos")

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    precio_min = df_estado['Volt_minimo'].min()
    estado_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Estado_Mapa'].iloc[0]
    cliente_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Cliente'].iloc[0]
    st.metric("💰 Precio más bajo", f"${precio_min:,.2f}", f"{estado_min} - {cliente_min}")
    
with col2:
    precio_max = df_estado['Volt_minimo'].max()
    estado_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Estado_Mapa'].iloc[0]
    cliente_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Cliente'].iloc[0]
    st.metric("💸 Precio más alto", f"${precio_max:,.2f}", f"{estado_max} - {cliente_max}")
    
with col3:
    precio_prom = df_estado['Volt_minimo'].mean()
    st.metric("📊 Precio promedio", f"${precio_prom:,.2f}")
    
with col4:
    st.metric("🏪 Estados con datos", len(df_estado))

# --- TABLA CON CLIENTE Y PRECIO ---
st.subheader("📋 Tabla de Precios Mínimos por Estado")

# Crear tabla con formato mejorado
df_tabla = df_estado[['Estado_Mapa', 'Cliente', 'Volt_minimo', 'Total_Tiendas']].copy()
df_tabla.columns = ['Estado', 'Cliente con precio mínimo', 'Precio Mínimo', 'Total Tiendas']
df_tabla = df_tabla.sort_values(by='Precio Mínimo', ascending=True)

# Formatear precios
df_tabla['Precio Mínimo'] = df_tabla['Precio Mínimo'].apply(lambda x: f"${x:,.2f}")

# Resaltar los precios más bajos y altos
def resaltar_precios(row):
    precio_limpio = float(row['Precio Mínimo'].replace('$', '').replace(',', ''))
    if precio_limpio == df_estado['Volt_minimo'].min():
        return ['background-color: #90EE90'] * len(row)  # Verde claro
    elif precio_limpio == df_estado['Volt_minimo'].max():
        return ['background-color: #FFB6C1'] * len(row)  # Rojo claro
    return [''] * len(row)

# Aplicar estilo
styled_df = df_tabla.style.apply(resaltar_precios, axis=1)

st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- GRÁFICO DE BARRAS ---
st.subheader("📈 Distribución de Precios Mínimos por Estado")

# Crear gráfico de barras con información del cliente
fig_bar = px.bar(
    df_tabla.sort_values(by='Precio Mínimo', ascending=False),
    x='Estado',
    y=df_tabla['Precio Mínimo'].str.replace('$', '').str.replace(',', '').astype(float),
    color='Precio Mínimo',
    color_continuous_scale='RdYlGn_r',
    title="Precios Mínimos por Estado (Ordenados de Mayor a Menor)",
    labels={'y': 'Precio Mínimo ($)', 'x': 'Estado'},
    text=df_tabla['Cliente con precio mínimo']
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

# --- TABLA CON TODAS LAS TIENDAS POR ESTADO (OPCIONAL) ---
with st.expander("🔍 Ver todas las tiendas por estado"):
    # Mostrar todas las tiendas con sus precios
    df_todas_tiendas = df[['ESTADO', 'Folio Emetrix', 'VOLT']].copy()
    df_todas_tiendas.columns = ['Estado', 'Cliente', 'Precio']
    df_todas_tiendas['Estado_Mapa'] = df_todas_tiendas['Estado'].map(mapeo_estados)
    df_todas_tiendas = df_todas_tiendas[['Estado_Mapa', 'Cliente', 'Precio']]
    df_todas_tiendas = df_todas_tiendas.sort_values(['Estado_Mapa', 'Precio'])
    df_todas_tiendas['Precio'] = df_todas_tiendas['Precio'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(df_todas_tiendas, use_container_width=True, hide_index=True)

# --- EXPORTAR DATOS ---
st.subheader("📥 Descargar Datos")

# Botón para descargar CSV de precios mínimos
csv_min = df_tabla.to_csv(index=False)
st.download_button(
    label="📥 Descargar precios mínimos (CSV)",
    data=csv_min,
    file_name="precios_minimos_por_estado.csv",
    mime="text/csv"
)

# Botón para descargar todas las tiendas
csv_all = df_todas_tiendas.to_csv(index=False) if 'df_todas_tiendas' in locals() else ""
if csv_all:
    st.download_button(
        label="📥 Descargar todas las tiendas (CSV)",
        data=csv_all,
        file_name="todas_las_tiendas_por_estado.csv",
        mime="text/csv"
    )

# Mostrar estados sin datos
estados_sin_datos = set(nombres_geojson) - set(df_estado['Estado_Mapa'].dropna())
if estados_sin_datos:
    st.info(f"ℹ️ Estados sin datos en el mapa: {', '.join(sorted(estados_sin_datos))}")
