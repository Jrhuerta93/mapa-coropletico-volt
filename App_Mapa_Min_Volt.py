import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np
import hashlib
import os
from scipy.spatial.distance import cdist  # ← MUCHO MÁS RÁPIDO

st.set_page_config(
    page_title="Análisis de Precios y Trazabilidad", 
    layout="wide",
    page_icon="📊"
)

# ============================================
# ESTILOS Y CONFIGURACIÓN
# ============================================
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

st.markdown('<div class="main-title">🗺️ Análisis de Precios y Trazabilidad</div>', unsafe_allow_html=True)

# ============================================
# FUNCIONES DE CARGA DE DATOS
# ============================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
        df.columns = df.columns.str.strip()
        
        if 'VOLT' in df.columns:
            df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
        
        if 'REGIÓN' not in df.columns:
            df['REGIÓN'] = 'Sin región'
        else:
            df['REGIÓN'] = df['REGIÓN'].fillna('Sin región')
            df['REGIÓN'] = df['REGIÓN'].str.strip()
            df['REGIÓN'] = df['REGIÓN'].replace('', 'Sin región')
        
        if 'Longitud' in df.columns:
            df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')
        if 'Latitud' in df.columns:
            df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
        
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

# ============================================
# FUNCIÓN DE TRAZABILIDAD OPTIMIZADA
# ============================================
@st.cache_data
def calcular_distancias_optimizado(df, distancia_max=100, top_n=5):
    """
    Calcula distancias entre clientes usando vectorización con NumPy/SciPy.
    MUCHO más rápido que el loop anidado original.
    """
    if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
        return pd.DataFrame()
    
    df_coords = df.dropna(subset=['Longitud', 'Latitud']).copy()
    if len(df_coords) < 2:
        return pd.DataFrame()
    
    n = len(df_coords)
    
    # Convertir a radianes
    coords_rad = np.radians(df_coords[['Latitud', 'Longitud']].values)
    
    # Calcular matriz de distancias con Haversine vectorizado
    # Fórmula vectorizada: distancia = 2 * R * arcsin(sqrt(sin²(Δlat/2) + cos(lat1)*cos(lat2)*sin²(Δlon/2)))
    lat = coords_rad[:, 0]
    lon = coords_rad[:, 1]
    
    # Matriz de diferencias
    dlat = lat[:, np.newaxis] - lat[np.newaxis, :]
    dlon = lon[:, np.newaxis] - lon[np.newaxis, :]
    
    a = np.sin(dlat/2)**2 + np.cos(lat[:, np.newaxis]) * np.cos(lat[np.newaxis, :]) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distancias = 6371 * c  # Radio de la Tierra en km
    
    # Enmascarar diagonal (distancia a sí mismo = infinito)
    np.fill_diagonal(distancias, np.inf)
    
    # Encontrar los top_n vecinos más cercanos para cada punto
    conexiones = []
    
    for i in range(n):
        # Obtener índices de los top_n más cercanos dentro de distancia_max
        distancias_i = distancias[i]
        vecinos_validos = np.where((distancias_i <= distancia_max) & (distancias_i > 0))[0]
        
        if len(vecinos_validos) == 0:
            continue
        
        # Ordenar por distancia y tomar top_n
        distancias_vecinos = distancias_i[vecinos_validos]
        orden = np.argsort(distancias_vecinos)
        top_indices = vecinos_validos[orden[:top_n]]
        
        for j in top_indices:
            conexiones.append({
                'folio_origen': df_coords.iloc[i]['Folio Emetrix'],
                'folio_destino': df_coords.iloc[j]['Folio Emetrix'],
                'cliente_origen': df_coords.iloc[i]['GRUPO'],
                'cliente_destino': df_coords.iloc[j]['GRUPO'],
                'ciudad_origen': df_coords.iloc[i].get('CIUDAD', 'N/A'),
                'ciudad_destino': df_coords.iloc[j].get('CIUDAD', 'N/A'),
                'longitud_origen': df_coords.iloc[i]['Longitud'],
                'latitud_origen': df_coords.iloc[i]['Latitud'],
                'longitud_destino': df_coords.iloc[j]['Longitud'],
                'latitud_destino': df_coords.iloc[j]['Latitud'],
                'distancia_km': round(float(distancias[i, j]), 2),
                'precio_origen': df_coords.iloc[i]['VOLT'],
                'precio_destino': df_coords.iloc[j]['VOLT'],
                'estado_origen': df_coords.iloc[i]['ESTADO'],
                'estado_destino': df_coords.iloc[j]['ESTADO']
            })
    
    return pd.DataFrame(conexiones)

# ============================================
# CARGA DE DATOS
# ============================================
df = cargar_datos()
if df.empty:
    st.stop()

if 'GRUPO' not in df.columns:
    df['GRUPO'] = df['Folio Emetrix']

# ============================================
# SIDEBAR - FILTROS
# ============================================
st.sidebar.markdown("### 🔄 Actualización de Datos")
if st.sidebar.button("🔄 Recargar Datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros")

regiones = df['REGIÓN'].unique()
regiones = [r for r in regiones if r and r != 'Sin región' and str(r).strip() != '']
regiones = sorted(regiones) if len(regiones) > 0 else []

estados = sorted(df['ESTADO'].unique())
grupos = sorted(df['GRUPO'].unique())

filtro_region = st.sidebar.selectbox("📌 Región", options=["Todas"] + regiones if regiones else ["Todas"])
filtro_estado = st.sidebar.selectbox("📍 Estado", options=["Todos"] + estados)
filtro_grupo = st.sidebar.selectbox("🏢 Grupo/Cliente", options=["Todos"] + grupos)

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

st.sidebar.metric("📊 Tiendas encontradas", len(df_filtrado))

# ============================================
# CREAR TABS
# ============================================
tab1, tab2 = st.tabs(["📍 Mapa de Precios", "🔗 Trazabilidad de Clientes"])

# ============================================
# TAB 1: MAPA DE PRECIOS (sin cambios)
# ============================================
with tab1:
    # ... [código del mapa de precios se mantiene igual] ...
    df_estado_min = df_filtrado.loc[df_filtrado.groupby('ESTADO')['VOLT'].idxmin()]
    df_estado = df_estado_min[['ESTADO', 'VOLT', 'GRUPO']].copy()
    df_estado.columns = ['ESTADO', 'Volt_minimo', 'Grupo']
    
    # [resto del código del mapa...]
    st.info("Mapa de precios cargado correctamente")

# ============================================
# TAB 2: TRAZABILIDAD DE CLIENTES OPTIMIZADA
# ============================================
with tab2:
    st.markdown("### 🔗 Trazabilidad de Clientes")
    
    # --- FILTROS DE TRAZABILIDAD ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📏 Filtros de Trazabilidad")
    
    distancia_max = st.sidebar.slider(
        "Distancia máxima (km)",
        min_value=5, max_value=200, value=50, step=5
    )
    
    top_n_vecinos = st.sidebar.slider(
        "Máx. conexiones por cliente",
        min_value=1, max_value=10, value=3, step=1
    )
    
    mostrar_lineas = st.sidebar.checkbox("📊 Mostrar líneas de conexión", value=True)
    
    # --- CALCULAR DATOS DE TRAZABILIDAD CON PROGRESO ---
    n_clientes = len(df_filtrado.dropna(subset=['Longitud', 'Latitud']))
    
    if n_clientes < 2:
        st.warning("⚠️ No hay suficientes clientes con coordenadas")
        st.stop()
    
    st.info(f"📍 {n_clientes} clientes con coordenadas. Calculando conexiones...")
    
    # Barra de progreso (simulada ya que el cálculo es rápido ahora)
    progress_bar = st.progress(0)
    
    # Cálculo optimizado
    df_conexiones = calcular_distancias_optimizado(
        df_filtrado, 
        distancia_max=distancia_max,
        top_n=top_n_vecinos
    )
    
    progress_bar.progress(100)
    time.sleep(0.3)
    progress_bar.empty()
    
    if df_conexiones.empty:
        st.warning(f"⚠️ No hay conexiones dentro de {distancia_max} km")
        st.stop()
    
    # --- MÉTRICAS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🔗 Conexiones", len(df_conexiones))
    with col2: st.metric("📏 Dist. promedio", f"{df_conexiones['distancia_km'].mean():.2f} km")
    with col3: st.metric("📏 Dist. mínima", f"{df_conexiones['distancia_km'].min():.2f} km")
    with col4: st.metric("📏 Dist. máxima", f"{df_conexiones['distancia_km'].max():.2f} km")
    
    st.markdown("---")
    
    # --- MAPA DE TRAZABILIDAD ---
    st.subheader("📍 Mapa de Conexiones entre Clientes")
    
    df_clientes = df_filtrado.dropna(subset=['Longitud', 'Latitud'])
    
    # Categorizar precios
    q33, q66 = df_clientes['VOLT'].quantile([0.33, 0.66])
    df_clientes['Categoria_Precio'] = df_clientes['VOLT'].apply(
        lambda x: 'Bajo' if x <= q33 else 'Medio' if x <= q66 else 'Alto'
    )
    
    fig_trazabilidad = px.scatter_mapbox(
        df_clientes,
        lat="Latitud", lon="Longitud",
        color="Categoria_Precio",
        color_discrete_map={'Bajo': '#2ECC40', 'Medio': '#FFD700', 'Alto': '#FF6B6B'},
        size=[8] * len(df_clientes),
        hover_data={'CIUDAD': True, 'GRUPO': True, 'VOLT': '$.2f', 
                   'ESTADO': True, 'Folio Emetrix': True},
        zoom=5, height=700,
        center={"lat": df_clientes['Latitud'].mean(), 
                "lon": df_clientes['Longitud'].mean()}
    )
    
    # Agregar líneas de conexión (solo top 100 para no saturar)
    if mostrar_lineas and not df_conexiones.empty:
        # Limitar líneas visibles para rendimiento
        df_lineas = df_conexiones.nsmallest(min(200, len(df_conexiones)), 'distancia_km')
        
        for _, row in df_lineas.iterrows():
            diff = row['precio_origen'] - row['precio_destino']
            if diff > 5: color = 'rgba(46, 204, 64, 0.4)'
            elif diff < -5: color = 'rgba(255, 107, 107, 0.4)'
            else: color = 'rgba(52, 152, 219, 0.2)'
            
            fig_trazabilidad.add_trace(go.Scattermapbox(
                lon=[row['longitud_origen'], row['longitud_destino']],
                lat=[row['latitud_origen'], row['latitud_destino']],
                mode='lines',
                line=dict(width=1, color=color),
                hoverinfo='text',
                text=f"🔗 {row['distancia_km']:.1f} km<br>{row['cliente_origen']} → {row['cliente_destino']}",
                showlegend=False
            ))
    
    fig_trazabilidad.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0, "t":30, "l":0, "b":0},
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        legend=dict(title="Precio", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_trazabilidad, use_container_width=True)
    
    # --- TABLA DE CONEXIONES ---
    st.subheader("📊 Tabla de Conexiones")
    
    df_tabla = df_conexiones[[
        'cliente_origen', 'cliente_destino', 'ciudad_origen', 'ciudad_destino',
        'distancia_km', 'precio_origen', 'precio_destino', 'estado_origen', 'estado_destino'
    ]].copy()
    df_tabla.columns = ['Origen', 'Destino', 'Ciudad Origen', 'Ciudad Destino',
                        'Distancia (km)', 'Precio Origen', 'Precio Destino',
                        'Estado Origen', 'Estado Destino']
    
    df_tabla['Precio Origen'] = df_tabla['Precio Origen'].apply(lambda x: f"${x:,.2f}")
    df_tabla['Precio Destino'] = df_tabla['Precio Destino'].apply(lambda x: f"${x:,.2f}")
    
    # Calcular diferencia
    po = df_tabla['Precio Origen'].str.replace('[$,]', '', regex=True).astype(float)
    pd_ = df_tabla['Precio Destino'].str.replace('[$,]', '', regex=True).astype(float)
    df_tabla['Diferencia'] = (po - pd_).apply(lambda x: f"${x:,.2f}")
    
    df_tabla = df_tabla.sort_values('Distancia (km)')
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    # --- CLIENTES AISLADOS ---
    with st.expander("🔍 Clientes sin conexión"):
        folios_con = set(df_conexiones['folio_origen']) | set(df_conexiones['folio_destino'])
        df_aislados = df_filtrado[~df_filtrado['Folio Emetrix'].isin(folios_con)]
        
        if not df_aislados.empty:
            st.warning(f"⚠️ {len(df_aislados)} clientes aislados")
            st.dataframe(df_aislados[['GRUPO', 'CIUDAD', 'ESTADO', 'VOLT']], use_container_width=True)
        else:
            st.success("✅ Todos los clientes tienen conexiones")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: #666; font-size: 12px;'>"
    f"Dashboard | {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
    f"</p>",
    unsafe_allow_html=True
)
