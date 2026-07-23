import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np
import time
import hashlib
import os

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Análisis de Precios y Trazabilidad", 
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS PARA OCULTAR ICONOS DE STREAMLIT
# ============================================
st.markdown("""
    <style>
    /* Ocultar el menú de hamburguesa (tres puntos arriba a la derecha) */
    #MainMenu {visibility: hidden;}
    
    /* Ocultar el icono de GitHub */
    .stAppDeployButton {display: none;}
    
    /* Ocultar el footer de "Made with Streamlit" */
    footer {visibility: hidden;}
    
    /* Ocultar la barra de herramientas de Streamlit */
    .stToolbar {visibility: hidden;}
    
    /* Ocultar el botón de compartir */
    .stApp a[href*="share.streamlit.io"] {display: none;}
    
    /* Ocultar elementos del header */
    header {visibility: hidden;}
    
    /* Ocultar el botón de deploy/github */
    button[kind="header"] {display: none;}
    
    /* Estilos personalizados del título */
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
# CONFIGURACIÓN DE BANDA DE PRECIOS
# ============================================
PRECIO_OBJETIVO = 235

RANGOS_SEMAFORO = [
    {'min': 0, 'max': 225, 'color': 'rgba(255, 107, 107, 0.18)', 'nombre': 'Rojo', 'descripcion': 'Abajo de 225 (crítico)'},
    {'min': 225, 'max': 230, 'color': 'rgba(255, 165, 0, 0.18)', 'nombre': 'Naranja', 'descripcion': '225-230 (riesgo/precaución)'},
    {'min': 230, 'max': 235, 'color': 'rgba(46, 204, 64, 0.18)', 'nombre': 'Verde', 'descripcion': '230-235 (saludable)'},
    {'min': 235, 'max': 300, 'color': 'rgba(66, 133, 244, 0.18)', 'nombre': 'Azul', 'descripcion': '+235 (sobre desempeño)'},
]

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
    if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
        return pd.DataFrame()
    
    df_coords = df.dropna(subset=['Longitud', 'Latitud']).copy()
    if len(df_coords) < 2:
        return pd.DataFrame()
    
    n = len(df_coords)
    coords_rad = np.radians(df_coords[['Latitud', 'Longitud']].values)
    
    lat = coords_rad[:, 0]
    lon = coords_rad[:, 1]
    
    dlat = lat[:, np.newaxis] - lat[np.newaxis, :]
    dlon = lon[:, np.newaxis] - lon[np.newaxis, :]
    
    a = np.sin(dlat/2)**2 + np.cos(lat[:, np.newaxis]) * np.cos(lat[np.newaxis, :]) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distancias = 6371 * c
    
    np.fill_diagonal(distancias, np.inf)
    
    conexiones = []
    
    for i in range(n):
        distancias_i = distancias[i]
        vecinos_validos = np.where((distancias_i <= distancia_max) & (distancias_i > 0))[0]
        
        if len(vecinos_validos) == 0:
            continue
        
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
# TAB 1: MAPA DE PRECIOS
# ============================================
with tab1:
    df_estado_min = df_filtrado.loc[df_filtrado.groupby('ESTADO')['VOLT'].idxmin()]
    df_estado = df_estado_min[['ESTADO', 'VOLT', 'GRUPO']].copy()
    df_estado.columns = ['ESTADO', 'Volt_minimo', 'Grupo']
    
    if 'REGIÓN' in df_filtrado.columns:
        df_estado = df_estado.merge(
            df_filtrado[['ESTADO', 'REGIÓN']].drop_duplicates('ESTADO'), 
            on='ESTADO', how='left'
        )
    
    tiendas_por_estado = df_filtrado.groupby('ESTADO').size().reset_index(name='Total_Tiendas')
    df_estado = df_estado.merge(tiendas_por_estado, on='ESTADO', how='left')
    
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
    
    TAMANO_TEXTO = 9
    
    df_estado['Texto_Mapa'] = df_estado.apply(
        lambda row: f"${row['Volt_minimo']:,.0f}" + ("🔴" if row['Es_Critico'] else ""),
        axis=1
    )
    
    # ============================================
    # CREAR HOVER TEXT CORRECTAMENTE
    # ============================================
    hover_texts = []
    for _, row in df_estado.iterrows():
        hover = f"<b>{row['Estado_Mapa']}</b><br>"
        hover += f"🏢 Grupo: {row['Grupo']}<br>"
        hover += f"💰 Precio: <b>${row['Volt_minimo']:,.2f}</b><br>"
        hover += f"📊 Tiendas: {row['Total_Tiendas']}"
        if 'REGIÓN' in row and pd.notna(row['REGIÓN']) and row['REGIÓN'] != 'Sin región':
            hover += f"<br>📍 Región: {row['REGIÓN']}"
        if row['Es_Critico']:
            hover += "<br>🔴 <b>¡PRECIO CRÍTICO!</b>"
        hover_texts.append(hover)
    
    df_estado['Hover_Texto'] = hover_texts
    
    geojson_data = cargar_geojson()
    if geojson_data is None:
        st.error("❌ No se pudo cargar el archivo GeoJSON")
    else:
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
            hovertemplate="%{customdata}<extra></extra>",
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
                    size=TAMANO_TEXTO,
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
                    size=20,
                    color='red',
                    symbol='circle',
                    opacity=0.15,
                    line=dict(width=1.5, color='darkred')
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
        # GRÁFICO DE ÁREA/LÍNEA CON BANDA DE PRECIOS Y SEMÁFORO
        # ============================================
        st.subheader("📈 Curva de Precios por Clientes vs Objetivo")
        
        df_linea = df_estado[['Estado_Mapa', 'Grupo', 'Volt_minimo']].copy()
        df_linea.columns = ['Estado', 'Grupo', 'Precio']
        df_linea = df_linea.sort_values('Precio', ascending=True).reset_index(drop=True)
        
        fig_linea = go.Figure()
        
        for rango in RANGOS_SEMAFORO:
            fig_linea.add_hrect(
                y0=rango['min'],
                y1=rango['max'],
                fillcolor=rango['color'],
                line_width=0,
                layer="below"
            )
        
        fig_linea.add_hline(
            y=PRECIO_OBJETIVO,
            line_dash="solid",
            line_color="#1a1a2e",
            line_width=2,
            layer="below"
        )
        
        fig_linea.add_annotation(
            x=1.0,
            y=PRECIO_OBJETIVO,
            xref='paper',
            yref='y',
            text=f"<b>🎯 ${PRECIO_OBJETIVO}</b>",
            showarrow=False,
            font=dict(size=11, color="#1a1a2e", family="Arial"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#1a1a2e",
            borderwidth=1,
            borderpad=4,
            xanchor='left',
            yanchor='bottom',
            xshift=10
        )
        
        fig_linea.add_trace(go.Scatter(
            x=df_linea['Estado'],
            y=df_linea['Precio'],
            fill='tozeroy',
            fillcolor='rgba(70, 130, 180, 0.25)',
            line=dict(color='#1a3a5c', width=2.5),
            mode='lines+markers+text',
            marker=dict(size=6, color='#1a3a5c', line=dict(width=1, color='white')),
            text=df_linea['Precio'].apply(lambda x: f"${x:.1f}"),
            textposition='top center',
            textfont=dict(size=9, color='#1a1a2e', family='Arial'),
            hovertemplate="<b>%{x}</b><br>💰 $%{y:,.2f}<br>🏢 %{customdata}<extra></extra>",
            customdata=df_linea['Grupo']
        ))
        
        y_min = max(170, df_linea['Precio'].min() - 8)
        y_max = min(250, df_linea['Precio'].max() + 8)
        
        fig_linea.update_yaxes(
            range=[y_min, y_max],
            dtick=5,
            tickprefix="$",
            tickformat=",.0f",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.06)',
            gridwidth=0.5,
            zeroline=False,
            title=dict(text='Precio ($)', font=dict(size=11))
        )
        
        fig_linea.update_xaxes(
            tickangle=-45,
            tickfont=dict(size=8),
            showgrid=False
        )
        
        fig_linea.update_layout(
            title=dict(
                text="Curva de Precios por Clientes vs Objetivo",
                font=dict(size=16, color="#1a1a2e", family="Arial")
            ),
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=520,
            margin=dict(l=70, r=150, t=70, b=110),
            annotations=[
                dict(
                    x=1.01,
                    y=0.98,
                    xref='paper',
                    yref='paper',
                    text="<b>Semáforo de Precios</b><br>" +
                         "<span style='color:#4285F4'>■</span> <b>Azul</b>: +$235 (sobre desempeño)<br>" +
                         "<span style='color:#2ECC40'>■</span> <b>Verde</b>: $230-235 (saludable)<br>" +
                         "<span style='color:#FFA500'>■</span> <b>Naranja</b>: $225-230 (riesgo)<br>" +
                         "<span style='color:#FF6B6B'>■</span> <b>Rojo</b>: <$225 (crítico)",
                    showarrow=False,
                    font=dict(size=10, family="Arial"),
                    align='left',
                    bgcolor='rgba(255,255,255,0.95)',
                    bordercolor='#cccccc',
                    borderwidth=1,
                    borderpad=8
                )
            ]
        )
        
        st.plotly_chart(fig_linea, use_container_width=True)
        
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
    
    n_clientes = len(df_filtrado.dropna(subset=['Longitud', 'Latitud']))
    
    if n_clientes < 2:
        st.warning("⚠️ No hay suficientes clientes con coordenadas")
        st.stop()
    
    st.info(f"📍 {n_clientes} clientes con coordenadas. Calculando conexiones...")
    
    progress_bar = st.progress(0)
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🔗 Conexiones", len(df_conexiones))
    with col2: st.metric("📏 Dist. promedio", f"{df_conexiones['distancia_km'].mean():.2f} km")
    with col3: st.metric("📏 Dist. mínima", f"{df_conexiones['distancia_km'].min():.2f} km")
    with col4: st.metric("📏 Dist. máxima", f"{df_conexiones['distancia_km'].max():.2f} km")
    
    st.markdown("---")
    
    st.subheader("📍 Mapa de Conexiones entre Clientes")
    
    df_clientes = df_filtrado.dropna(subset=['Longitud', 'Latitud'])
    
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
        hover_data={
            'CIUDAD': True, 
            'GRUPO': True, 
            'VOLT': '$.2f', 
            'ESTADO': True, 
            'Folio Emetrix': True
        },
        zoom=5, height=700,
        center={"lat": df_clientes['Latitud'].mean(), 
                "lon": df_clientes['Longitud'].mean()}
    )
    
    if mostrar_lineas and not df_conexiones.empty:
        df_lineas = df_conexiones.nsmallest(min(200, len(df_conexiones)), 'distancia_km')
        
        for _, row in df_lineas.iterrows():
            diff = row['precio_origen'] - row['precio_destino']
            if diff > 5: 
                color = 'rgba(46, 204, 64, 0.4)'
            elif diff < -5: 
                color = 'rgba(255, 107, 107, 0.4)'
            else: 
                color = 'rgba(52, 152, 219, 0.2)'
            
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
    
    st.subheader("📊 Tabla de Conexiones")
    
    df_tabla_conexiones = df_conexiones[[
        'cliente_origen', 'cliente_destino', 'ciudad_origen', 'ciudad_destino',
        'distancia_km', 'precio_origen', 'precio_destino', 'estado_origen', 'estado_destino'
    ]].copy()
    df_tabla_conexiones.columns = ['Origen', 'Destino', 'Ciudad Origen', 'Ciudad Destino',
                        'Distancia (km)', 'Precio Origen', 'Precio Destino',
                        'Estado Origen', 'Estado Destino']
    
    df_tabla_conexiones['Precio Origen'] = df_tabla_conexiones['Precio Origen'].apply(lambda x: f"${x:,.2f}")
    df_tabla_conexiones['Precio Destino'] = df_tabla_conexiones['Precio Destino'].apply(lambda x: f"${x:,.2f}")
    
    po = df_tabla_conexiones['Precio Origen'].str.replace('[$,]', '', regex=True).astype(float)
    pd_ = df_tabla_conexiones['Precio Destino'].str.replace('[$,]', '', regex=True).astype(float)
    df_tabla_conexiones['Diferencia'] = (po - pd_).apply(lambda x: f"${x:,.2f}")
    
    df_tabla_conexiones = df_tabla_conexiones.sort_values('Distancia (km)')
    st.dataframe(df_tabla_conexiones, use_container_width=True, hide_index=True)
    
    with st.expander("🔍 Clientes sin conexión"):
        folios_con = set(df_conexiones['folio_origen']) | set(df_conexiones['folio_destino'])
        df_aislados = df_filtrado[~df_filtrado['Folio Emetrix'].isin(folios_con)]
        
        if not df_aislados.empty:
            st.warning(f"⚠️ {len(df_aislados)} clientes aislados")
            st.dataframe(df_aislados[['GRUPO', 'CIUDAD', 'ESTADO', 'VOLT']], use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todos los clientes tienen conexiones")

# ============================================
# EXPORTAR DATOS
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if 'df_conexiones' in locals() and not df_conexiones.empty:
        csv = df_tabla_conexiones.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Conexiones (CSV)",
            data=csv,
            file_name="conexiones_clientes.csv",
            mime="text/csv",
            use_container_width=True
        )

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
