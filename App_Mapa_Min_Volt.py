import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np
from scipy.spatial import distance_matrix
from scipy.cluster.hierarchy import linkage, fcluster
import hashlib
import os

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
    .tab-content {
        padding: 20px 0;
    }
    .critical-price {
        background-color: #ff6b6b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ Análisis de Precios y Trazabilidad</div>', unsafe_allow_html=True)

# ============================================
# FUNCIONES DE CARGA DE DATOS
# ============================================
@st.cache_data
def obtener_hash_archivo():
    """Obtiene el hash del archivo CSV para detectar cambios"""
    try:
        with open("datos_tiendas.csv", "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

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
        
        # Asegurar columnas de coordenadas
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
# FUNCIONES DE TRAZABILIDAD
# ============================================
def calcular_distancias(df):
    """Calcula las distancias entre todos los clientes"""
    if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
        return None
    
    df_coords = df.dropna(subset=['Longitud', 'Latitud'])
    if len(df_coords) < 2:
        return None
    
    coords = df_coords[['Longitud', 'Latitud']].values
    dist_matrix = distance_matrix(coords, coords) * 111
    
    conexiones = []
    for i in range(len(coords)):
        distancias = dist_matrix[i]
        indices_cercanos = np.argsort(distancias)[1:6]  # Top 5 más cercanos
        
        for j in indices_cercanos:
            if distancias[j] <= 100:
                conexiones.append({
                    'folio_origen': df_coords.iloc[i]['Folio Emetrix'],
                    'folio_destino': df_coords.iloc[j]['Folio Emetrix'],
                    'cliente_origen': df_coords.iloc[i]['GRUPO'],
                    'cliente_destino': df_coords.iloc[j]['GRUPO'],
                    'ciudad_origen': df_coords.iloc[i]['CIUDAD'] if 'CIUDAD' in df_coords.columns else 'N/A',
                    'ciudad_destino': df_coords.iloc[j]['CIUDAD'] if 'CIUDAD' in df_coords.columns else 'N/A',
                    'longitud_origen': df_coords.iloc[i]['Longitud'],
                    'latitud_origen': df_coords.iloc[i]['Latitud'],
                    'longitud_destino': df_coords.iloc[j]['Longitud'],
                    'latitud_destino': df_coords.iloc[j]['Latitud'],
                    'distancia_km': distancias[j],
                    'precio_origen': df_coords.iloc[i]['VOLT'],
                    'precio_destino': df_coords.iloc[j]['VOLT'],
                    'estado_origen': df_coords.iloc[i]['ESTADO'],
                    'estado_destino': df_coords.iloc[j]['ESTADO']
                })
    
    return pd.DataFrame(conexiones)

def detectar_clusters(df, distancia_max=50):
    """Detecta clusters de clientes cercanos"""
    if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
        return df
    
    df_coords = df.dropna(subset=['Longitud', 'Latitud'])
    if len(df_coords) < 2:
        df['Cluster'] = -1
        return df
    
    coords = df_coords[['Longitud', 'Latitud']].values
    dist_matrix = distance_matrix(coords, coords) * 111
    
    # Usar clustering jerárquico
    linkage_matrix = linkage(coords, method='ward')
    clusters = fcluster(linkage_matrix, t=distancia_max, criterion='distance')
    
    # Asignar clusters al dataframe original
    df['Cluster'] = -1
    for idx, cluster_id in zip(df_coords.index, clusters):
        df.loc[idx, 'Cluster'] = int(cluster_id)
    
    return df

# ============================================
# CARGA DE DATOS
# ============================================
df = cargar_datos()
if df.empty:
    st.stop()

# Verificar si existe la columna GRUPO
if 'GRUPO' not in df.columns:
    df['GRUPO'] = df['Folio Emetrix']

# ============================================
# SIDEBAR - FILTROS Y ACTUALIZACIÓN
# ============================================
st.sidebar.markdown("### 🔄 Actualización de Datos")
if st.sidebar.button("🔄 Recargar Datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros")

# Obtener valores únicos para filtros
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

# Mostrar regiones disponibles
if filtro_region == "Todas":
    regiones_filtradas = df_filtrado['REGIÓN'].unique()
    regiones_filtradas = [r for r in regiones_filtradas if r and r != 'Sin región']
    if regiones_filtradas:
        st.sidebar.markdown(f"**Regiones presentes:** {', '.join(sorted(regiones_filtradas))}")

# ============================================
# CREAR TABS
# ============================================
tab1, tab2 = st.tabs(["📍 Mapa de Precios", "🔗 Trazabilidad de Clientes"])

# ============================================
# TAB 1: MAPA DE PRECIOS (CÓDIGO EXISTENTE)
# ============================================
with tab1:
    # --- IDENTIFICAR PRECIO MÍNIMO POR ESTADO ---
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
    
    # Función para color de texto
    def get_text_color(value, min_val, max_val):
        if max_val == min_val:
            return 'white'
        normalized = (value - min_val) / (max_val - min_val)
        if normalized > 0.55:
            return 'white'
        else:
            return 'black'
    
    # Identificar precios críticos
    precio_minimo_global = df_estado['Volt_minimo'].min()
    precio_maximo_global = df_estado['Volt_minimo'].max()
    rango_precio = precio_maximo_global - precio_minimo_global
    
    umbral_critico = precio_minimo_global + (rango_precio * 0.25)
    df_estado['Es_Critico'] = df_estado['Volt_minimo'] <= umbral_critico
    
    # Preparar datos para el mapa
    df_estado['Color_Texto'] = df_estado['Volt_minimo'].apply(
        lambda x: get_text_color(x, precio_minimo_global, precio_maximo_global)
    )
    
    df_estado['Texto_Mapa'] = df_estado.apply(
        lambda row: f"${row['Volt_minimo']:,.2f}" + (" 🔴" if row['Es_Critico'] else ""),
        axis=1
    )
    
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
    else:
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
        
        # Agregar mapa coropleto
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
        
        # Calcular centroides
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
        df_con_coords = df_estado.dropna(subset=['lon', 'lat']).drop_duplicates(subset=['Estado_Mapa'])
        
        # Agregar etiquetas
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
        
        # Agregar marcadores para precios críticos
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
        
        # Configurar layout
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

# ============================================
# TAB 2: TRAZABILIDAD DE CLIENTES (NUEVO COMPLETO)
# ============================================
with tab2:
    st.markdown("### 🔗 Trazabilidad de Clientes")
    
    # --- FILTROS DE TRAZABILIDAD ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📏 Filtros de Trazabilidad")
    
    distancia_max = st.sidebar.slider(
        "Distancia máxima (km)",
        min_value=5,
        max_value=100,
        value=50,
        step=5
    )
    
    mostrar_lineas = st.sidebar.checkbox("📊 Mostrar líneas de conexión", value=True)
    mostrar_etiquetas = st.sidebar.checkbox("🏷️ Mostrar etiquetas de clientes", value=True)
    mostrar_clusters = st.sidebar.checkbox("🎯 Mostrar clusters", value=True)
    
    # --- CALCULAR DATOS DE TRAZABILIDAD ---
    df_conexiones = calcular_distancias(df_filtrado)
    
    if df_conexiones is None or df_conexiones.empty:
        st.warning("⚠️ No hay suficientes datos con coordenadas para calcular distancias")
        st.stop()
    
    # Filtrar por distancia
    df_conexiones = df_conexiones[df_conexiones['distancia_km'] <= distancia_max]
    
    if df_conexiones.empty:
        st.warning(f"⚠️ No hay conexiones dentro de {distancia_max} km con los filtros actuales")
        st.stop()
    
    # Detectar clusters
    df_clusters = detectar_clusters(df_filtrado, distancia_max=distancia_max)
    
    # --- MÉTRICAS DE TRAZABILIDAD ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🔗 Conexiones", len(df_conexiones))
    
    with col2:
        dist_prom = df_conexiones['distancia_km'].mean()
        st.metric("📏 Dist. promedio", f"{dist_prom:.2f} km")
    
    with col3:
        dist_min = df_conexiones['distancia_km'].min()
        st.metric("📏 Dist. mínima", f"{dist_min:.2f} km")
    
    with col4:
        dist_max = df_conexiones['distancia_km'].max()
        st.metric("📏 Dist. máxima", f"{dist_max:.2f} km")
    
    with col5:
        num_clusters = df_clusters['Cluster'].nunique() - 1 if 'Cluster' in df_clusters.columns else 0
        st.metric("🎯 Clusters", num_clusters)
    
    st.markdown("---")
    
    # --- MAPA DE TRAZABILIDAD ---
    st.subheader("📍 Mapa de Conexiones entre Clientes")
    
    # Preparar datos para el mapa
    df_clientes = df_filtrado.dropna(subset=['Longitud', 'Latitud'])
    
    # Asignar colores según cluster
    if mostrar_clusters and 'Cluster' in df_clusters.columns:
        cluster_colors = {
            -1: 'gray',
            1: '#FF6B6B',
            2: '#4ECDC4',
            3: '#45B7D1',
            4: '#96CEB4',
            5: '#FFEAA7',
            6: '#DDA0DD',
            7: '#FF8A5C',
            8: '#A29BFE',
            9: '#FD79A8',
            10: '#00CEC9'
        }
        # Asegurar que todos los clientes tengan cluster
        colores_clientes = df_clientes.apply(
            lambda row: cluster_colors.get(row['Cluster'], 'gray') if pd.notna(row['Cluster']) else 'gray',
            axis=1
        )
    else:
        # Colores según precio
        colores_clientes = []
        for precio in df_clientes['VOLT']:
            if precio <= df_clientes['VOLT'].quantile(0.33):
                colores_clientes.append('#2ECC40')  # Verde
            elif precio <= df_clientes['VOLT'].quantile(0.66):
                colores_clientes.append('#FFD700')  # Amarillo
            else:
                colores_clientes.append('#FF6B6B')  # Rojo
    
    # Crear figura
    fig_trazabilidad = go.Figure()
    
    # 1. Agregar puntos de clientes
    fig_trazabilidad.add_trace(go.Scattermapbox(
        lon=df_clientes['Longitud'],
        lat=df_clientes['Latitud'],
        mode='markers+text' if mostrar_etiquetas else 'markers',
        text=df_clientes['GRUPO'] if mostrar_etiquetas else None,
        textposition='top center',
        textfont=dict(size=9, color='black', family='Arial'),
        marker=dict(
            size=12,
            color=colores_clientes,
            opacity=0.9,
            line=dict(width=1, color='white')
        ),
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      "🏢 Grupo: %{customdata[1]}<br>" +
                      "💰 Precio: <b>$%{customdata[2]:,.2f}</b><br>" +
                      "📍 Estado: %{customdata[3]}<br>" +
                      "📊 Folio: %{customdata[4]}" +
                      ("<br>🎯 Cluster: %{customdata[5]}" if mostrar_clusters else "") +
                      "<extra></extra>",
        customdata=df_clientes[['CIUDAD', 'GRUPO', 'VOLT', 'ESTADO', 'Folio Emetrix', 'Cluster']].values if 'Cluster' in df_clientes.columns 
                    else df_clientes[['CIUDAD', 'GRUPO', 'VOLT', 'ESTADO', 'Folio Emetrix']].values,
        name='Clientes'
    ))
    
    # 2. Agregar líneas de conexión
    if mostrar_lineas:
        # Agrupar conexiones para evitar duplicados
        conexiones_unicas = df_conexiones.drop_duplicates(subset=['folio_origen', 'folio_destino'])
        
        for _, row in conexiones_unicas.iterrows():
            # Color según diferencia de precio
            diff_precio = row['precio_origen'] - row['precio_destino']
            if diff_precio > 5:
                color_linea = 'rgba(46, 204, 64, 0.6)'  # Verde - Origen más barato
            elif diff_precio < -5:
                color_linea = 'rgba(255, 107, 107, 0.6)'  # Rojo - Destino más barato
            else:
                color_linea = 'rgba(52, 152, 219, 0.4)'  # Azul - Precios similares
            
            # Grosor según distancia
            width = max(1, min(4, int(5 - (row['distancia_km'] / 25))))
            
            fig_trazabilidad.add_trace(go.Scattermapbox(
                lon=[row['longitud_origen'], row['longitud_destino']],
                lat=[row['latitud_origen'], row['latitud_destino']],
                mode='lines',
                line=dict(
                    width=width,
                    color=color_linea
                ),
                hovertemplate="<b>🔗 Conexión</b><br>" +
                              "📏 Distancia: <b>%{customdata[0]:.2f} km</b><br>" +
                              "🏢 Origen: %{customdata[1]}<br>" +
                              "🏢 Destino: %{customdata[2]}<br>" +
                              "💰 Precio Origen: $%{customdata[3]:,.2f}<br>" +
                              "💰 Precio Destino: $%{customdata[4]:,.2f}<br>" +
                              "💱 Diferencia: $%{customdata[5]:,.2f}<br>" +
                              "<extra></extra>",
                customdata=[[
                    row['distancia_km'],
                    row['cliente_origen'],
                    row['cliente_destino'],
                    row['precio_origen'],
                    row['precio_destino'],
                    row['precio_origen'] - row['precio_destino']
                ]],
                showlegend=False,
                name='Conexiones'
            ))
    
    # Configurar layout
    fig_trazabilidad.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(
                lat=df_clientes['Latitud'].mean() if not df_clientes.empty else 23.6345,
                lon=df_clientes['Longitud'].mean() if not df_clientes.empty else -102.5528
            ),
            zoom=5
        ),
        margin={"r":0, "t":30, "l":0, "b":0},
        height=750,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            font_color="#2c3e50",
            bordercolor="#2c3e50"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    st.plotly_chart(fig_trazabilidad, use_container_width=True)
    
    # --- TABLA DE CONEXIONES ---
    st.subheader("📊 Tabla de Conexiones y Distancias")
    
    # Crear tabla formateada
    df_tabla_conexiones = df_conexiones[['cliente_origen', 'cliente_destino', 'ciudad_origen', 'ciudad_destino',
                                          'distancia_km', 'precio_origen', 'precio_destino', 
                                          'estado_origen', 'estado_destino']].copy()
    df_tabla_conexiones.columns = ['Cliente Origen', 'Cliente Destino', 'Ciudad Origen', 'Ciudad Destino',
                                    'Distancia (km)', 'Precio Origen', 'Precio Destino', 
                                    'Estado Origen', 'Estado Destino']
    
    # Formatear precios
    df_tabla_conexiones['Precio Origen'] = df_tabla_conexiones['Precio Origen'].apply(lambda x: f"${x:,.2f}")
    df_tabla_conexiones['Precio Destino'] = df_tabla_conexiones['Precio Destino'].apply(lambda x: f"${x:,.2f}")
    
    # Calcular diferencia
    df_tabla_conexiones['Diferencia'] = df_tabla_conexiones['Precio Origen'].str.replace('$', '').str.replace(',', '').astype(float) - \
                                         df_tabla_conexiones['Precio Destino'].str.replace('$', '').str.replace(',', '').astype(float)
    df_tabla_conexiones['Diferencia'] = df_tabla_conexiones['Diferencia'].apply(lambda x: f"${x:,.2f}")
    
    # Ordenar por distancia
    df_tabla_conexiones = df_tabla_conexiones.sort_values('Distancia (km)', ascending=True)
    
    # Destacar filas con menor distancia
    def color_conexiones(row):
        if row['Distancia (km)'] <= df_tabla_conexiones['Distancia (km)'].quantile(0.25):
            return ['background-color: #cce5ff; font-weight: bold'] * len(row)
        elif row['Distancia (km)'] >= df_tabla_conexiones['Distancia (km)'].quantile(0.75):
            return ['background-color: #ffe0e0'] * len(row)
        return [''] * len(row)
    
    styled_conexiones = df_tabla_conexiones.style.apply(color_conexiones, axis=1)
    st.dataframe(styled_conexiones, use_container_width=True, hide_index=True)
    
    # --- ANÁLISIS DE CLUSTERS ---
    if mostrar_clusters and 'Cluster' in df_clusters.columns:
        st.subheader("🎯 Análisis de Clusters")
        
        # Estadísticas por cluster
        df_cluster_stats = df_clusters[df_clusters['Cluster'] != -1].groupby('Cluster').agg({
            'GRUPO': 'count',
            'VOLT': ['mean', 'min', 'max'],
            'ESTADO': lambda x: x.nunique()
        }).round(2)
        
        df_cluster_stats.columns = ['Clientes', 'Precio Promedio', 'Precio Mínimo', 'Precio Máximo', 'Estados']
        df_cluster_stats = df_cluster_stats.sort_values('Clientes', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Estadísticas por Cluster")
            st.dataframe(df_cluster_stats, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Distribución de Clusters")
            cluster_counts = df_clusters[df_clusters['Cluster'] != -1]['Cluster'].value_counts().sort_index()
            
            fig_clusters = px.bar(
                x=cluster_counts.index,
                y=cluster_counts.values,
                title="Número de Clientes por Cluster",
                labels={'x': 'Cluster', 'y': 'Clientes'},
                color=cluster_counts.values,
                color_continuous_scale='Blues'
            )
            fig_clusters.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_clusters, use_container_width=True)
    
    # --- CLIENTES SIN CONEXIÓN ---
    with st.expander("🔍 Clientes sin conexión (aislados)"):
        # Identificar clientes que no tienen conexiones
        folios_con_conexion = set(df_conexiones['folio_origen']).union(set(df_conexiones['folio_destino']))
        df_aislados = df_filtrado[~df_filtrado['Folio Emetrix'].isin(folios_con_conexion)]
        df_aislados = df_aislados[['GRUPO', 'CIUDAD', 'ESTADO', 'VOLT']].copy()
        df_aislados.columns = ['Grupo', 'Ciudad', 'Estado', 'Precio']
        df_aislados['Precio'] = df_aislados['Precio'].apply(lambda x: f"${x:,.2f}")
        
        if not df_aislados.empty:
            st.warning(f"⚠️ {len(df_aislados)} clientes sin conexiones dentro de {distancia_max} km")
            st.dataframe(df_aislados, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todos los clientes tienen al menos una conexión")

# ============================================
# EXPORTAR DATOS
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    # Exportar datos de conexiones
    if 'df_conexiones' in locals() and not df_conexiones.empty:
        csv_conexiones = df_tabla_conexiones.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Conexiones (CSV)",
            data=csv_conexiones,
            file_name="conexiones_clientes.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 12px;'>"
    "Dashboard desarrollado con ❤️ | Datos actualizados al: " + 
    pd.Timestamp.now().strftime('%d/%m/%Y %H:%M') +
    "</p>",
    unsafe_allow_html=True
)
