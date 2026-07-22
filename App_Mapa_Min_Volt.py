import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np
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
# FUNCIONES DE TRAZABILIDAD
# ============================================
def calcular_distancias_manual(df):
    """Calcula las distancias entre todos los clientes usando Haversine"""
    if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
        return None
    
    df_coords = df.dropna(subset=['Longitud', 'Latitud'])
    if len(df_coords) < 2:
        return None
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    conexiones = []
    n = len(df_coords)
    
    for i in range(n):
        distancias = []
        for j in range(n):
            if i != j:
                dist = haversine(
                    df_coords.iloc[i]['Latitud'], df_coords.iloc[i]['Longitud'],
                    df_coords.iloc[j]['Latitud'], df_coords.iloc[j]['Longitud']
                )
                distancias.append((j, dist))
        
        distancias.sort(key=lambda x: x[1])
        
        for j, dist in distancias[:5]:
            if dist <= 100:
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
                    'distancia_km': dist,
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
# SIDEBAR - FILTROS Y ACTUALIZACIÓN
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

# ============================================
# CREAR TABS
# ============================================
tab1, tab2 = st.tabs(["📍 Mapa de Precios", "🔗 Trazabilidad de Clientes"])

# ============================================
# TAB 1: MAPA DE PRECIOS (VERSIÓN QUE FUNCIONA)
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
    
    def get_text_color(value, min_val, max_val):
        if max_val == min_val:
            return 'white'
        normalized = (value - min_val) / (max_val - min_val)
        if normalized > 0.55:
            return 'white'
        else:
            return 'black'
    
    precio_minimo_global = df_estado['Volt_minimo'].min()
    precio_maximo_global = df_estado['Volt_minimo'].max()
    rango_precio = precio_maximo_global - precio_minimo_global
    
    umbral_critico = precio_minimo_global + (rango_precio * 0.25)
    df_estado['Es_Critico'] = df_estado['Volt_minimo'] <= umbral_critico
    
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

# ============================================
# TAB 2: TRAZABILIDAD DE CLIENTES
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
    
    # --- CALCULAR DATOS DE TRAZABILIDAD ---
    df_conexiones = calcular_distancias_manual(df_filtrado)
    
    if df_conexiones is None or df_conexiones.empty:
        st.warning("⚠️ No hay suficientes datos con coordenadas para calcular distancias")
        st.stop()
    
    df_conexiones = df_conexiones[df_conexiones['distancia_km'] <= distancia_max]
    
    if df_conexiones.empty:
        st.warning(f"⚠️ No hay conexiones dentro de {distancia_max} km con los filtros actuales")
        st.stop()
    
    # --- MÉTRICAS DE TRAZABILIDAD ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔗 Conexiones", len(df_conexiones))
    
    with col2:
        dist_prom = df_conexiones['distancia_km'].mean()
        st.metric("📏 Dist. promedio", f"{dist_prom:.2f} km")
    
    with col3:
        dist_min = df_conexiones['distancia_km'].min()
        st.metric("📏 Dist. mínima", f"{dist_min:.2f} km")
    
    with col4:
        dist_max_val = df_conexiones['distancia_km'].max()
        st.metric("📏 Dist. máxima", f"{dist_max_val:.2f} km")
    
    st.markdown("---")
    
    # --- MAPA DE TRAZABILIDAD USANDO PLOTLY EXPRESS ---
    st.subheader("📍 Mapa de Conexiones entre Clientes")
    
    df_clientes = df_filtrado.dropna(subset=['Longitud', 'Latitud'])
    
    # Crear columna de color según precio
    df_clientes['Categoria_Precio'] = df_clientes['VOLT'].apply(
        lambda x: 'Bajo' if x <= df_clientes['VOLT'].quantile(0.33) 
        else 'Medio' if x <= df_clientes['VOLT'].quantile(0.66) 
        else 'Alto'
    )
    
    # Crear mapa con plotly express
    fig_trazabilidad = px.scatter_mapbox(
        df_clientes,
        lat="Latitud",
        lon="Longitud",
        color="Categoria_Precio",
        color_discrete_map={
            'Bajo': '#2ECC40',
            'Medio': '#FFD700',
            'Alto': '#FF6B6B'
        },
        size=[10] * len(df_clientes),
        hover_data={
            'CIUDAD': True,
            'GRUPO': True,
            'VOLT': '$.2f',
            'ESTADO': True,
            'Folio Emetrix': True,
            'Categoria_Precio': False
        },
        title="Clientes y sus conexiones (Verde=Bajo, Amarillo=Medio, Rojo=Alto)",
        zoom=5,
        height=700,
        center={
            "lat": df_clientes['Latitud'].mean() if not df_clientes.empty else 23.6345,
            "lon": df_clientes['Longitud'].mean() if not df_clientes.empty else -102.5528
        }
    )
    
    # Agregar líneas de conexión
    if mostrar_lineas:
        conexiones_unicas = df_conexiones.drop_duplicates(subset=['folio_origen', 'folio_destino'])
        
        for _, row in conexiones_unicas.iterrows():
            diff_precio = row['precio_origen'] - row['precio_destino']
            if diff_precio > 5:
                color_linea = 'rgba(46, 204, 64, 0.6)'
            elif diff_precio < -5:
                color_linea = 'rgba(255, 107, 107, 0.6)'
            else:
                color_linea = 'rgba(52, 152, 219, 0.4)'
            
            fig_trazabilidad.add_trace(go.Scattermapbox(
                lon=[row['longitud_origen'], row['longitud_destino']],
                lat=[row['latitud_origen'], row['latitud_destino']],
                mode='lines',
                line=dict(width=2, color=color_linea),
                hoverinfo='text',
                text=f"🔗 Conexión<br>📏 Distancia: {row['distancia_km']:.2f} km<br>🏢 {row['cliente_origen']} → {row['cliente_destino']}<br>💰 ${row['precio_origen']:.2f} → ${row['precio_destino']:.2f}<br>💱 Diferencia: ${row['precio_origen'] - row['precio_destino']:.2f}",
                showlegend=False
            ))
    
    # Actualizar layout
    fig_trazabilidad.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0, "t":30, "l":0, "b":0},
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
        legend=dict(
            title="Precio",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_trazabilidad, use_container_width=True)
    
    # --- TABLA DE CONEXIONES ---
    st.subheader("📊 Tabla de Conexiones y Distancias")
    
    df_tabla_conexiones = df_conexiones[['cliente_origen', 'cliente_destino', 'ciudad_origen', 'ciudad_destino',
                                          'distancia_km', 'precio_origen', 'precio_destino', 
                                          'estado_origen', 'estado_destino']].copy()
    df_tabla_conexiones.columns = ['Cliente Origen', 'Cliente Destino', 'Ciudad Origen', 'Ciudad Destino',
                                    'Distancia (km)', 'Precio Origen', 'Precio Destino', 
                                    'Estado Origen', 'Estado Destino']
    
    df_tabla_conexiones['Precio Origen'] = df_tabla_conexiones['Precio Origen'].apply(lambda x: f"${x:,.2f}")
    df_tabla_conexiones['Precio Destino'] = df_tabla_conexiones['Precio Destino'].apply(lambda x: f"${x:,.2f}")
    
    # Calcular diferencia
    precio_origen_num = df_tabla_conexiones['Precio Origen'].str.replace('$', '').str.replace(',', '').astype(float)
    precio_destino_num = df_tabla_conexiones['Precio Destino'].str.replace('$', '').str.replace(',', '').astype(float)
    df_tabla_conexiones['Diferencia'] = (precio_origen_num - precio_destino_num).apply(lambda x: f"${x:,.2f}")
    
    df_tabla_conexiones = df_tabla_conexiones.sort_values('Distancia (km)', ascending=True)
    
    def color_conexiones(row):
        if row['Distancia (km)'] <= df_tabla_conexiones['Distancia (km)'].quantile(0.25):
            return ['background-color: #cce5ff; font-weight: bold'] * len(row)
        return [''] * len(row)
    
    styled_conexiones = df_tabla_conexiones.style.apply(color_conexiones, axis=1)
    st.dataframe(styled_conexiones, use_container_width=True, hide_index=True)
    
    # --- CLIENTES SIN CONEXIÓN ---
    with st.expander("🔍 Clientes sin conexión (aislados)"):
        folios_con_conexion = set(df_conexiones['folio_origen']).union(set(df_conexiones['folio_destino']))
        df_aislados = df_filtrado[~df_filtrado['Folio Emetrix'].isin(folios_con_conexion)]
        df_aislados = df_aislados[['GRUPO', 'CIUDAD', 'ESTADO', 'VOLT']].copy()
        df_aislados.columns = ['Grupo', 'Ciudad', 'Estado', 'Precio']
        df_aislados['Precio'] = df_aislados['Precio'].apply(lambda x: f"${x:,.2f}")
        
        if not df_aislados.empty:
            st.warning
