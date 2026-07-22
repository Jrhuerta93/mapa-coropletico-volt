import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np

st.set_page_config(
    page_title="Volt Mínimo por Estado", 
    layout="wide",
    page_icon="📊"
)

# Estilo personalizado para mejor presentación
st.markdown("""
    <style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #1a1a2e;
        padding: 20px 0;
        text-align: center;
        border-bottom: 3px solid #16213e;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stMetric {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Estilo para precios críticos */
    .critical-price {
        background-color: #ff6b6b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Título con estilo
st.markdown('<div class="main-title">🗺️ Mapa de Precios Mínimos por Estado</div>', unsafe_allow_html=True)

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
    try:
        with open('mexico.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
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
st.sidebar.markdown("### 🔍 Filtros")
st.sidebar.markdown("---")

# Crear opciones para filtros
regiones = df['REGION'].unique() if 'REGION' in df.columns else []
estados = df['ESTADO'].unique()
grupos = df['GRUPO'].unique()

# Filtros en sidebar con mejor estilo
filtro_region = st.sidebar.selectbox(
    "📌 Región",
    options=["Todas"] + sorted(regiones.tolist()) if len(regiones) > 0 else ["Todas"]
)

filtro_estado = st.sidebar.selectbox(
    "📍 Estado",
    options=["Todos"] + sorted(estados.tolist())
)

filtro_grupo = st.sidebar.selectbox(
    "🏢 Grupo/Cliente",
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
st.sidebar.metric("📊 Tiendas encontradas", len(df_filtrado))

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

# ============================================
# IDENTIFICAR PRECIOS CRÍTICOS (los más bajos)
# ============================================
precio_minimo_global = df_estado['Volt_minimo'].min()
precio_maximo_global = df_estado['Volt_minimo'].max()
rango_precio = precio_maximo_global - precio_minimo_global

# Un precio es crítico si está en el 25% inferior
umbral_critico = precio_minimo_global + (rango_precio * 0.25)
df_estado['Es_Critico'] = df_estado['Volt_minimo'] <= umbral_critico

# ============================================
# CONFIGURACIÓN DE ESTILO MEJORADO
# ============================================
# Texto con mejor contraste - NEGRO para mejor visibilidad
TEXTO_TAMAÑO = 11
TEXTO_COLOR = 'black'  # <--- CAMBIADO A NEGRO PARA MEJOR CONTRASTE

# Crear texto para mostrar SOLO el precio
df_estado['Texto_Mapa'] = df_estado.apply(
    lambda row: f"<b>${row['Volt_minimo']:,.2f}</b>" + 
                (" 🔴" if row['Es_Critico'] else ""),
    axis=1
)

# Crear texto para hover con indicador de precio crítico
df_estado['Hover_Texto'] = df_estado.apply(
    lambda row: f"<b>{row['Estado_Mapa']}</b><br>" +
                f"🏢 Grupo: {row['Grupo']}<br>" +
                f"💰 Precio: <b>${row['Volt_minimo']:,.2f}</b><br>" +
                f"📊 Tiendas: {row['Total_Tiendas']}<br>" +
                ("🔴 <b>PRECIO CRÍTICO - OFERTA EXCEPCIONAL</b>" if row['Es_Critico'] else ""),
    axis=1
)

# Cargar GeoJSON
geojson_data = cargar_geojson()
if geojson_data is None:
    st.error("❌ No se pudo cargar el archivo GeoJSON")
    st.stop()

# --- MÉTRICAS PRINCIPALES ---
st.markdown("### 📊 Resumen Ejecutivo")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    precio_min = df_filtrado['VOLT'].min()
    st.metric("💰 Precio más bajo", f"${precio_min:,.2f}", delta="⭐ Oferta crítica")

with col2:
    precio_max = df_filtrado['VOLT'].max()
    st.metric("💸 Precio más alto", f"${precio_max:,.2f}", delta="Precio premium")

with col3:
    precio_prom = df_filtrado['VOLT'].mean()
    st.metric("📊 Precio promedio", f"${precio_prom:,.2f}")

with col4:
    total_estados = len(df_estado)
    st.metric("📍 Estados activos", total_estados)

with col5:
    total_criticos = df_estado['Es_Critico'].sum()
    st.metric("🔴 Precios críticos", total_criticos, delta="Ofertas especiales")

st.markdown("---")

# --- CREAR MAPA CON ESTILO BLUES Y MEJOR CONTRASTE ---
st.subheader("📍 Mapa de Precios Mínimos por Estado")

# Paleta Blues con mejor contraste
COLOR_SCALE = 'Blues'

# Crear figura con go.Figure
fig = go.Figure()

# 1. Agregar el mapa coropleto con estilo Blues
fig.add_trace(go.Choropleth(
    geojson=geojson_data,
    locations=df_estado['Estado_Mapa'],
    z=df_estado['Volt_minimo'],
    featureidkey="properties.name",
    colorscale=COLOR_SCALE,
    zmin=df_estado['Volt_minimo'].min(),
    zmax=df_estado['Volt_minimo'].max(),
    marker_line_width=1.5,
    marker_line_color='white',
    colorbar=dict(
        title=dict(
            text="Volt Mínimo ($)",
            side="right",
            font=dict(size=14, family="Arial", color="#2c3e50")
        ),
        tickprefix="$",
        tickformat=",.0f",
        thickness=25,
        len=0.8,
        x=1.02,
        tickfont=dict(size=12),
        bgcolor="rgba(255,255,255,0.8)"
    ),
    hovertemplate="%{customdata[0]}<extra></extra>",
    customdata=df_estado['Hover_Texto'].values,
    showscale=True
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

# 3. Agregar etiquetas de precio con TEXTO NEGRO para mejor contraste
fig.add_trace(go.Scattergeo(
    lon=df_con_coords['lon'],
    lat=df_con_coords['lat'],
    mode='text',
    text=df_con_coords['Texto_Mapa'],
    textfont=dict(
        size=TEXTO_TAMAÑO,
        color=TEXTO_COLOR,  # <--- NEGRO para mejor visibilidad
        family='Arial, sans-serif'
    ),
    textposition='middle center',
    hoverinfo='skip',
    showlegend=False
))

# 4. Agregar marcadores para precios críticos (círculos rojos)
df_criticos = df_con_coords[df_con_coords['Es_Critico']]
if not df_criticos.empty:
    fig.add_trace(go.Scattergeo(
        lon=df_criticos['lon'],
        lat=df_criticos['lat'],
        mode='markers',
        marker=dict(
            size=20,
            color='red',
            symbol='circle',
            opacity=0.3,
            line=dict(width=2, color='darkred')
        ),
        hoverinfo='skip',
        showlegend=False,
        name='Precios críticos'
    ))

# Configurar el layout con mejor estética
fig.update_geos(
    fitbounds="locations",
    visible=False,
    showcoastlines=True,
    coastlinecolor="white",
    coastlinewidth=1.5,
    showland=True,
    landcolor="#f0f0f0",
    showocean=True,
    oceancolor="#e8f4f8",
    showcountries=False,
    showframe=False
)

# Agregar créditos como en la imagen
fig.update_layout(
    margin={"r":30, "t":30, "l":0, "b":30},
    height=750,
    geo=dict(
        projection_type='mercator',
        showframe=False,
        showcoastlines=True,
        coastlinecolor="white",
    ),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Arial",
        font_color="#2c3e50",
        bordercolor="#2c3e50"
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    annotations=[
        dict(
            x=0.5,
            y=-0.08,
            xref='paper',
            yref='paper',
            text='Con tecnología de Bing © GeoNames, Microsoft, TomTom',
            showarrow=False,
            font=dict(size=10, color='#666666')
        )
    ]
)

# Mostrar el mapa
st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DATOS CON PRECIOS CRÍTICOS DESTACADOS ---
st.subheader("📊 Detalle por Estado")

# Crear tabla con mejor formato
df_tabla = df_estado[['Estado_Mapa', 'Grupo', 'Volt_minimo', 'Total_Tiendas', 'Es_Critico']].copy()
df_tabla.columns = ['Estado', 'Grupo con mejor precio', 'Precio Mínimo', 'Total Tiendas', 'Precio Crítico']
df_tabla = df_tabla.sort_values('Precio Mínimo', ascending=True)

# Formatear precios
df_tabla['Precio Mínimo'] = df_tabla['Precio Mínimo'].apply(lambda x: f"${x:,.2f}")
df_tabla['Precio Crítico'] = df_tabla['Precio Crítico'].apply(lambda x: '🔴 Sí' if x else '')

# Función para colorear filas según precio
def color_rows(row):
    if row['Precio Crítico'] == '🔴 Sí':
        return ['background-color: #ff6b6b; color: white; font-weight: bold'] * len(row)
    return [''] * len(row)

styled_df = df_tabla.style.apply(color_rows, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- GRÁFICO DE BARRAS CON DESTAQUE DE CRÍTICOS ---
st.subheader("📈 Distribución de Precios por Estado")

# Crear gráfico de barras
df_bar = df_tabla.copy()
df_bar['Precio Numérico'] = df_bar['Precio Mínimo'].str.replace('$', '').str.replace(',', '').astype(float)
df_bar = df_bar.sort_values('Precio Numérico', ascending=True)

# Colores personalizados: rojo para críticos, azul para el resto
colors = ['#ff6b6b' if row['Precio Crítico'] == '🔴 Sí' else '#3182bd' for _, row in df_bar.iterrows()]

fig_bar = px.bar(
    df_bar,
    x='Estado',
    y='Precio Numérico',
    color='Precio Numérico',
    color_continuous_scale='Blues',
    title="Precios Mínimos por Estado - De mejor a peor oferta",
    labels={'y': 'Precio Mínimo ($)', 'x': 'Estado'},
    text='Grupo con mejor precio',
    height=500
)

# Cambiar color de barras críticas a rojo
fig_bar.update_traces(
    textposition='outside',
    textfont=dict(size=10, family="Arial"),
    marker_line_color='white',
    marker_line_width=1.5
)

# Añadir anotaciones para precios críticos
for i, row in df_bar.iterrows():
    if row['Precio Crítico'] == '🔴 Sí':
        fig_bar.add_annotation(
            x=row['Estado'],
            y=row['Precio Numérico'],
            text="🔴 CRÍTICO",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#ff6b6b",
            font=dict(size=10, color="#ff6b6b", weight='bold'),
            ax=0,
            ay=-30
        )

fig_bar.update_layout(
    xaxis_tickangle=-45,
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family="Arial", size=12, color="#2c3e50"),
    title_font=dict(size=16, color="#1a1a2e"),
    coloraxis_colorbar=dict(
        title="Precio",
        tickprefix="$",
        tickformat=",.0f"
    ),
    margin=dict(l=50, r=50, t=80, b=100)
)

st.plotly_chart(fig_bar, use_container_width=True)

# --- INSIGHTS Y STORYTELLING MEJORADO ---
st.markdown("---")
st.subheader("📖 Insights y Storytelling")

# Generar insights automáticos
precio_min = df_estado['Volt_minimo'].min()
precio_max = df_estado['Volt_minimo'].max()
estado_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Estado_Mapa'].iloc[0]
estado_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Estado_Mapa'].iloc[0]
grupo_min = df_estado[df_estado['Volt_minimo'] == precio_min]['Grupo'].iloc[0]
grupo_max = df_estado[df_estado['Volt_minimo'] == precio_max]['Grupo'].iloc[0]

# Contar críticos por región
criticos_por_region = df_estado[df_estado['Es_Critico']].groupby('REGION').size() if 'REGION' in df_estado.columns else {}

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    ### 🔴 Precios Críticos (Ofertas Excepcionales)
    
    **{estado_min}** ofrece el precio más bajo con **${precio_min:,.2f}**
    
    *Clave:* {grupo_min} es el proveedor con la mejor oferta.
    
    **Total de precios críticos:** {total_criticos} estados
    """)
    
    if criticos_por_region:
        st.markdown("**Distribución por región:**")
        for region, count in criticos_por_region.items():
            st.markdown(f"- {region}: {count} estado(s)")

with col2:
    st.markdown(f"""
    ### 📊 Análisis de Oportunidades
    
    **{estado_max}** tiene el precio más alto con **${precio_max:,.2f}**
    
    *Diferencia:* ${precio_max - precio_min:,.2f} ({((precio_max - precio_min) / precio_min * 100):.0f}% más caro)
    
    **Recomendación:**
    - ✅ Aprovechar precios críticos en {estado_min}
    - 📈 Negociar mejoras en {estado_max}
    - 🎯 Enfocar estrategia en {total_criticos} estados con mejores precios
    """)

# --- EXPORTAR DATOS ---
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    csv = df_tabla.to_csv(index=False)
    st.download_button(
        label="📥 Descargar Datos (CSV)",
        data=csv,
        file_name="precios_minimos_por_estado.csv",
        mime="text/csv",
        use_container_width=True
    )
