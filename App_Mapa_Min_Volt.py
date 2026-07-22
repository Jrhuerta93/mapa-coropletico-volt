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
    .stMetric {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ Mapa de Precios Mínimos por Estado</div>', unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
        df.columns = df.columns.str.strip()
        
        if 'VOLT' in df.columns:
            df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
        
        # Asegurar que la columna REGIÓN existe y tiene datos
        if 'REGIÓN' not in df.columns:
            df['REGIÓN'] = 'Sin región'
        else:
            df['REGIÓN'] = df['REGIÓN'].fillna('Sin región')
            df['REGIÓN'] = df['REGIÓN'].str.strip()
            df['REGIÓN'] = df['REGIÓN'].replace('', 'Sin región')
        
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

# Obtener regiones únicas
regiones = df['REGIÓN'].unique()
regiones = [r for r in regiones if r and r != 'Sin región' and str(r).strip() != '']
regiones = sorted(regiones) if len(regiones) > 0 else []

estados = sorted(df['ESTADO'].unique())
grupos = sorted(df['GRUPO'].unique())

filtro_region = st.sidebar.selectbox(
    "📌 Región",
    options=["Todas"] + regiones if regiones else ["Todas"]
)

filtro_estado = st.sidebar.selectbox(
    "📍 Estado",
    options=["Todos"] + estados
)

filtro_grupo = st.sidebar.selectbox(
    "🏢 Grupo/Cliente",
    options=["Todos"] + grupos
)

# Aplicar filtros
df_filtrado = df.copy()

if filtro_region != "Todas" and filtro_region:
    df_filtrado = df_filtrado[df_filtrado['REGIÓN'] == filtro_region]

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ESTADO'] == filtro_estado]

if filtro_grupo != "Todos":
    df_filtrado = df_filtrado[df_filtrado['GRUPO'] == filtro_grupo]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.metric("📊 Tiendas encontradas", len(df_filtrado))

# Mostrar regiones disponibles en los datos filtrados
if filtro_region == "Todas":
    regiones_filtradas = df_filtrado['REGIÓN'].unique()
    regiones_filtradas = [r for r in regiones_filtradas if r and r != 'Sin región']
    if regiones_filtradas:
        st.sidebar.markdown(f"**Regiones presentes:** {', '.join(sorted(regiones_filtradas))}")

# --- IDENTIFICAR LA TIENDA CON PRECIO MÍNIMO POR ESTADO ---
df_estado_min = df_filtrado.loc[df_filtrado.groupby('ESTADO')['VOLT'].idxmin()]

df_estado = df_estado_min[['ESTADO', 'VOLT', 'GRUPO']].copy()
df_estado.columns = ['ESTADO', 'Volt_minimo', 'Grupo']

if 'REGIÓN' in df_filtrado.columns:
    df_estado = df_estado.merge(
        df_filtrado[['ESTADO', 'REGIÓN']].drop_duplicates('ESTADO'), 
        on='ESTADO', 
        how='left'
    )

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
# FUNCIÓN PARA DETERMINAR COLOR DE TEXTO
# ============================================
def get_text_color(value, min_val, max_val):
    if max_val == min_val:
        return 'white'
    
    normalized = (value - min_val) / (max_val - min_val)
    
    if normalized > 0.55:
        return 'white'
    else:
        return 'black'

# ============================================
# IDENTIFICAR PRECIOS CRÍTICOS
# ============================================
precio_minimo_global = df_estado['Volt_minimo'].min()
precio_maximo_global = df_estado['Volt_minimo'].max()
rango_precio = precio_maximo_global - precio_minimo_global

umbral_critico = precio_minimo_global + (rango_precio * 0.25)
df_estado['Es_Critico'] = df_estado['Volt_minimo'] <= umbral_critico

# ============================================
# CREAR TEXTO PARA HOVER Y MAPA - CORREGIDO
# ============================================
df_estado['Color_Texto'] = df_estado['Volt_minimo'].apply(
    lambda x: get_text_color(x, precio_minimo_global, precio_maximo_global)
)

df_estado['Texto_Mapa'] = df_estado.apply(
    lambda row: f"${row['Volt_minimo']:,.2f}" + 
                (" 🔴" if row['Es_Critico'] else ""),
    axis=1
)

# ============================================
# HOVER COMPLETO - CORREGIDO (USANDO 'REGIÓN' CON ACENTO)
# ============================================
df_estado['Hover_Texto'] = df_estado.apply(
    lambda row: f"<b>{row['Estado_Mapa']}</b><br>" +
                f"🏢 Grupo: {row['Grupo']}<br>" +
                f"💰 Precio: <b>${row['Volt_minimo']:,.2f}</b><br>" +
                f"📊 Tiendas: {row['Total_Tiendas']}" +
                (f"<br>📍 Región: {row['REGIÓN']}" if 'REGIÓN' in row and pd.notna(row['REGIÓN']) and row['REGIÓN'] != 'Sin región' else "") +
                ("<br>🔴 <b>¡PRECIO CRÍTICO!</b>" if row['Es_Critico'] else ""),
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
    st.metric("💰 Precio más bajo", f"${precio_min:,.2f}")

with col2:
    precio_max = df_filtrado['VOLT'].max()
    st.metric("💸 Precio más alto", f"${precio_max:,.2f}")

with col3:
    precio_prom = df_filtrado['VOLT'].mean()
    st.metric("📊 Precio promedio", f"${precio_prom:,.2f}")

with col4:
    total_estados = len(df_estado)
    st.metric("📍 Estados activos", total_estados)

with col5:
    total_criticos = df_estado['Es_Critico'].sum()
    st.metric("🔴 Precios críticos", total_criticos)

st.markdown("---")

# --- CREAR MAPA ---
st.subheader("📍 Mapa de Precios Mínimos por Estado")

COLOR_SCALE = 'Blues'

fig = go.Figure()

# 1. Agregar el mapa coropleto
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

# 2. Calcular centroides
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

df_estado['lon'] = df_estado['Estado_Mapa'].map(lambda x: centroides.get(x, (None, None))[0])
df_estado['lat'] = df_estado['Estado_Mapa'].map(lambda x: centroides.get(x, (None, None))[1])

# ============================================
# LIMPIAR DATOS DUPLICADOS - EVITAR ENCIMAMIENTO
# ============================================
# Eliminar duplicados por estado para que solo haya una etiqueta por estado
df_con_coords = df_estado.dropna(subset=['lon', 'lat']).drop_duplicates(subset=['Estado_Mapa'])

# 3. Agregar etiquetas de precio - UNA SOLA POR ESTADO
for _, row in df_con_coords.iterrows():
    fig.add_trace(go.Scattergeo(
        lon=[row['lon']],
        lat=[row['lat']],
        mode='text',
        text=[row['Texto_Mapa']],
        textfont=dict(
            size=11,
            color=row['Color_Texto'],
            family='Arial, sans-serif',
            weight='bold'
        ),
        textposition='middle center',
        hoverinfo='skip',
        showlegend=False
    ))

# 4. Agregar marcadores para precios críticos
df_criticos = df_con_coords[df_con_coords['Es_Critico']]
if not df_criticos.empty:
    fig.add_trace(go.Scattergeo(
        lon=df_criticos['lon'],
        lat=df_criticos['lat'],
        mode='markers',
        marker=dict(
            size=25,
            color='red',
            symbol='circle',
            opacity=0.2,
            line=dict(width=2, color='darkred')
        ),
        hoverinfo='skip',
        showlegend=False
    ))

# Configurar el layout
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

st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DATOS ---
st.subheader("📊 Detalle por Estado")

df_tabla = df_estado[['Estado_Mapa', 'Grupo', 'Volt_minimo', 'Total_Tiendas', 'Es_Critico', 'REGIÓN']].copy()
df_tabla.columns = ['Estado', 'Grupo con mejor precio', 'Precio Mínimo', 'Total Tiendas', 'Precio Crítico', 'Región']
df_tabla = df_tabla.sort_values('Precio Mínimo', ascending=True)

df_tabla['Precio Mínimo'] = df_tabla['Precio Mínimo'].apply(lambda x: f"${x:,.2f}")
df_tabla['Precio Crítico'] = df_tabla['Precio Crítico'].apply(lambda x: '🔴 Sí' if x else '')

def color_rows(row):
    if row['Precio Crítico'] == '🔴 Sí':
        return ['background-color: #ff6b6b; color: white; font-weight: bold'] * len(row)
    return [''] * len(row)

styled_df = df_tabla.style.apply(color_rows, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- GRÁFICO DE BARRAS ---
st.subheader("📈 Distribución de Precios por Estado")

df_bar = df_tabla.copy()
df_bar['Precio Numérico'] = df_bar['Precio Mínimo'].str.replace('$', '').str.replace(',', '').astype(float)
df_bar = df_bar.sort_values('Precio Numérico', ascending=True)

bar_colors = ['#ff6b6b' if row['Precio Crítico'] == '🔴 Sí' else '#3182bd' for _, row in df_bar.iterrows()]

fig_bar = go.Figure()

fig_bar.add_trace(go.Bar(
    x=df_bar['Estado'],
    y=df_bar['Precio Numérico'],
    text=df_bar['Grupo con mejor precio'],
    textposition='outside',
    textfont=dict(size=10),
    marker_color=bar_colors,
    marker_line_color='white',
    marker_line_width=1.5,
    hovertemplate="<b>%{x}</b><br>" +
                  "Precio: $%{y:,.2f}<br>" +
                  "Grupo: %{text}<br>" +
                  "<extra></extra>"
))

fig_bar.update_layout(
    title="Precios Mínimos por Estado - De mejor a peor oferta",
    xaxis_tickangle=-45,
    yaxis_title="Precio Mínimo ($)",
    xaxis_title="Estado",
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family="Arial", size=12, color="#2c3e50"),
    title_font=dict(size=16, color="#1a1a2e"),
    height=500,
    margin=dict(l=50, r=50, t=80, b=100)
)

st.plotly_chart(fig_bar, use_container_width=True)

# --- INSIGHTS Y STORYTELLING ---
st.markdown("---")
st.subheader("📖 Insights y Storytelling")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    ### 🎯 Precios Críticos Identificados
    
    **Umbral de precio crítico:** ${umbral_critico:,.2f}
    
    **Estados con precios críticos:**
    """)
    
    criticos = df_estado[df_estado['Es_Critico']]
    if not criticos.empty:
        for _, row in criticos.iterrows():
            st.markdown(f"- **{row['Estado_Mapa']}**: ${row['Volt_minimo']:,.2f} ({row['Grupo']})")
    else:
        st.markdown("*No hay precios críticos en el rango actual*")

with col2:
    st.markdown(f"""
    ### 📊 Análisis Estadístico
    
    - **Precio más bajo:** ${precio_minimo_global:,.2f}
    - **Precio más alto:** ${precio_maximo_global:,.2f}
    - **Rango:** ${rango_precio:,.2f}
    - **Precio promedio:** ${df_estado['Volt_minimo'].mean():,.2f}
    - **Mediana:** ${df_estado['Volt_minimo'].median():,.2f}
    
    **Oportunidades:**
    - 🟢 {df_estado[df_estado['Es_Critico']].shape[0]} estados con ofertas excepcionales
    - 🟡 {df_estado[~df_estado['Es_Critico']].shape[0]} estados con precios estándar
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
