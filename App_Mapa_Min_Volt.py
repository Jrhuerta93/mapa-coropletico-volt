import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("️ Mapa Coroplético: Volt Mínimo por Estado")
st.markdown("Análisis de precios mínimos y densidad de tiendas por entidad federativa.")

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
        st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
    except Exception as e:
        st.error(f"❌ Error al cargar CSV: {e}")
        return pd.DataFrame()
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Mostrar columnas disponibles para depuración
    st.write("📋 **Columnas encontradas:**", list(df.columns))
    
    # Asegurar que VOLT sea numérico
    if 'VOLT' in df.columns:
        df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
    else:
        st.error("❌ No se encontró la columna 'VOLT' en el CSV")
        return pd.DataFrame()
        
    return df

df = cargar_datos()

if df.empty:
    st.stop()

# ==========================================
# 3. PROCESAMIENTO Y MAPEO DE ESTADOS
# ==========================================
# Agrupar por estado
df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count')
).reset_index()

st.write(f"📊 **Estados únicos en datos:** {len(df_estado)}")
st.write("Estados encontrados:", df_estado['ESTADO'].tolist())

# Mapeo CORREGIDO de estados (nombres exactos del GeoJSON)
mapeo_estados = {
    'BAJA CALIFORNIA SUR': 'Baja California Sur',
    'CDMX': 'Ciudad de México',
    'CIUDAD DE MÉXICO': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'México',
    'ESTADO DE MÉXICO': 'México',
    'MÉXICO': 'México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACÁN': 'Michoacán',
    'MICHOACAN': 'Michoacán',
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
    'VERACRUZ': 'Veracruz',
    'VERACRUZ DE IGNACIO DE LA LLAVE': 'Veracruz',
    'YUCATAN': 'Yucatán',
    'YUCATÁN': 'Yucatán',
    'ZACATECAS': 'Zacatecas',
    'AGUASCALIENTES': 'Aguascalientes',
    'BAJA CALIFORNIA': 'Baja California',
    'CAMPECHE': 'Campeche',
    'COLIMA': 'Colima',
    'DURANGO': 'Durango',
    'GUERRERO': 'Guerrero',
    'NAYARIT': 'Nayarit',
    'PUEBLA': 'Puebla',
    'QUINTANA ROO': 'Quintana Roo',
    'SINALOA': 'Sinaloa',
    'TAMAULIPAS': 'Tamaulipas',
    'TLAXCALA': 'Tlaxcala'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# Verificar cuántos estados se mapearon correctamente
estados_mapeados = df_estado['Estado_Mapa'].notna().sum()
estados_sin_mapear = df_estado[df_estado['Estado_Mapa'].isna()]['ESTADO'].tolist()

if estados_sin_mapear:
    st.warning(f"⚠️ {len(estados_sin_mapear)} estados sin mapear: {estados_sin_mapear}")

st.write(f"✅ **{estados_mapeados} de {len(df_estado)} estados mapeados correctamente**")

# ==========================================
# 4. MAPA COROPLÉTICO
# ==========================================
st.subheader(" Distribución de Precio Volt Mínimo por Estado")

# Intentar cargar GeoJSON
try:
    geojson_url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/master/mexico.json"
    response = requests.get(geojson_url)
    geojson_data = response.json()
    st.success("✅ GeoJSON cargado correctamente")
except:
    st.error("❌ No se pudo cargar el GeoJSON")
    st.stop()

# Crear el mapa
fig = px.choropleth(
    df_estado,
    geojson=geojson_data,
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

# Ajustar el mapa
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. TABLA DE DATOS
# ==========================================
st.subheader(" Resumen de Datos por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
