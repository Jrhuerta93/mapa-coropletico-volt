import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Mapa Coroplético Volt", layout="wide")
st.title("🗺️ Mapa Coroplético: Precio Volt Mínimo por Estado")
st.markdown("Visualización de la diferencia de precios mínimos por entidad federativa.")

# ==========================================
# 2. CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data
def cargar_datos():
    try:
        # Ajusta el nombre si tu archivo se llama diferente
        df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
    except FileNotFoundError:
        st.error("❌ No se encontró 'datos_tiendas.csv'.")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    
    # Función para limpiar moneda (quita $, comas y paréntesis de negativos)
    def limpiar_moneda(valor):
        if pd.isna(valor): return 0.0
        val_str = str(valor).strip()
        if not val_str: return 0.0
        es_negativo = val_str.startswith('(') and val_str.endswith(')')
        if es_negativo: val_str = val_str[1:-1]
        val_str = val_str.replace('$', '').replace(',', '').strip()
        try:
            return -float(val_str) if es_negativo else float(val_str)
        except ValueError:
            return 0.0

    # Limpiar la columna VOLT (usa el nombre exacto de tu CSV)
    if 'VOLT' in df.columns:
        df['VOLT'] = df['VOLT'].apply(limpiar_moneda)
    elif 'Volt' in df.columns:
        df['VOLT'] = df['Volt'].apply(limpiar_moneda)
        
    return df

df = cargar_datos()
if df.empty:
    st.stop()

# ==========================================
# 3. PROCESAMIENTO Y AGRUPACIÓN
# ==========================================
# Agrupar por ESTADO para obtener el Volt mínimo y el conteo de tiendas
df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count') # Usa la columna de ID única
).reset_index()

# Mapeo de nombres: Tu CSV usa abreviaciones, el mapa usa nombres completos
mapeo_estados = {
    'BAJA CALIFORNIA SUR': 'Baja California Sur',
    'CDMX': 'Ciudad de México',
    'CHIAPAS': 'Chiapas',
    'CHIHUAHUA': 'Chihuahua',
    'EDO MEX': 'Estado de México',
    'GUANAJUATO': 'Guanajuato',
    'HIDALGO': 'Hidalgo',
    'JALISCO': 'Jalisco',
    'MICHOACÁN': 'Michoacán',
    'MORELOS': 'Morelos',
    'NUEVO LEON': 'Nuevo León',
    'OAXACA': 'Oaxaca',
    'PUEBLA': 'Puebla',
    'QUERETARO': 'Querétaro',
    'SAN LUIS POTOSI': 'San Luis Potosí',
    'SAN LUIS POTOSÍ': 'San Luis Potosí',
    'SONORA': 'Sonora',
    'TABASCO': 'Tabasco',
    'TLAXCALA': 'Tlaxcala',
    'TOLUCA': 'Estado de México', # Toluca es ciudad, se suma al Estado de México
    'VALLE DE MEXICO': 'Estado de México',
    'VERACRUZ': 'Veracruz'
}

df_estado['Estado_Mapa'] = df_estado['ESTADO'].map(mapeo_estados)

# ==========================================
# 4. GENERAR MAPA COROPLÉTICO (PLOTLY)
# ==========================================
# URL pública del GeoJSON de México (no necesitas subir este archivo a Git)
geojson_url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/master/mexico.json"

fig = px.choropleth(
    df_estado,
    geojson=geojson_url,
    locations='Estado_Mapa',
    color='Volt_minimo',
    featureidkey="properties.name",
    color_continuous_scale="Blues", # Escala de colores igual a tu imagen
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

# Ajustar el mapa para que solo muestre México
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

# Mostrar en Streamlit
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. TABLA DE RESUMEN (Como en tu segunda imagen)
# ==========================================
st.subheader("📊 Resumen de Datos por Estado")
df_tabla = df_estado[['Estado_Mapa', 'Volt_minimo', 'Tiendas']].copy()
df_tabla.columns = ['Estado', 'Volt Mínimo', 'Tiendas']
df_tabla = df_tabla.sort_values(by='Volt Mínimo', ascending=True)

# Formatear la columna de dinero para que se vea bonita en la tabla
df_tabla['Volt Mínimo'] = df_tabla['Volt Mínimo'].apply(lambda x: f"${x:,.2f}")

st.dataframe(df_tabla, use_container_width=True, hide_index=True)
