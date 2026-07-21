import streamlit as st
import pandas as pd
import plotly.express as px
import json

# ==================== CONFIGURACIÓN ====================
st.set_page_config(page_title="Mapa Volt Mínimo", layout="wide")
st.title("🗺️ Distribución de Precio Volt Mínimo por Estado")

# ==================== CARGA DE DATOS ====================
@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos_tiendas.csv")
    return df

df = cargar_datos()

# ==================== PROCESAMIENTO ====================
# Calcular Volt mínimo por estado
volt_min_por_estado = df.groupby("Estado")["Volt"].min().reset_index()
volt_min_por_estado.columns = ["Estado", "Volt_Minimo"]

# Contar tiendas por estado
tiendas_por_estado = df.groupby("Estado").size().reset_index(name="Num_Tiendas")

# Unir datos
datos_mapa = volt_min_por_estado.merge(tiendas_por_estado, on="Estado")

# ==================== MAPEO DE NOMBRES ====================
# Mapeo de nombres para que coincidan con el GeoJSON
mapeo_estados = {
    "Aguascalientes": "Aguascalientes",
    "Baja California": "Baja California",
    "Baja California Sur": "Baja California Sur",
    "Campeche": "Campeche",
    "Chiapas": "Chiapas",
    "Chihuahua": "Chihuahua",
    "CDMX": "Ciudad de México",
    "Ciudad de México": "Ciudad de México",
    "Coahuila": "Coahuila",
    "Colima": "Colima",
    "Durango": "Durango",
    "Estado de México": "México",
    "México": "México",
    "Guanajuato": "Guanajuato",
    "Guerrero": "Guerrero",
    "Hidalgo": "Hidalgo",
    "Jalisco": "Jalisco",
    "Michoacán": "Michoacán",
    "Morelos": "Morelos",
    "Nayarit": "Nayarit",
    "Nuevo León": "Nuevo León",
    "Oaxaca": "Oaxaca",
    "Puebla": "Puebla",
    "Querétaro": "Querétaro",
    "Quintana Roo": "Quintana Roo",
    "San Luis Potosí": "San Luis Potosí",
    "Sinaloa": "Sinaloa",
    "Sonora": "Sonora",
    "Tabasco": "Tabasco",
    "Tamaulipas": "Tamaulipas",
    "Tlaxcala": "Tlaxcala",
    "Veracruz": "Veracruz",
    "Yucatán": "Yucatán",
    "Zacatecas": "Zacatecas"
}

# Aplicar mapeo
datos_mapa["Estado_Normalizado"] = datos_mapa["Estado"].map(mapeo_estados)

# Eliminar estados no mapeados
datos_mapa_limpio = datos_mapa.dropna(subset=["Estado_Normalizado"])

# ==================== CARGAR GEOJSON LOCAL ====================
@st.cache_data
def cargar_geojson():
    try:
        with open("mexico.json", "r", encoding="utf-8") as f:
            geojson = json.load(f)
        return geojson
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo mexico.json")
        return None
    except json.JSONDecodeError:
        st.error("❌ El archivo mexico.json no es un JSON válido")
        return None

geojson = cargar_geojson()

# ==================== CREAR MAPA ====================
if geojson is not None and not datos_mapa_limpio.empty:
    fig = px.choropleth(
        datos_mapa_limpio,
        geojson=geojson,
        locations="Estado_Normalizado",
        featureidkey="properties.name",
        color="Volt_Minimo",
        hover_data={
            "Estado_Normalizado": True,
            "Volt_Minimo": ":.2f",
            "Num_Tiendas": True,
            "Estado": False  # Ocultar columna original
        },
        labels={
            "Volt_Minimo": "Precio Mínimo (Volt)",
            "Num_Tiendas": "Número de Tiendas",
            "Estado_Normalizado": "Estado"
        },
        color_continuous_scale="Blues",
        title="Distribución de Volt Mínimo por Estado",
        height=700
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        coloraxis_colorbar={
            "title": "Volt Mínimo",
            "tickprefix": "$",
            "ticksuffix": " MXN"
        }
    )

    # ==================== MOSTRAR EN STREAMLIT ====================
    col1, col2 = st.columns([3, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Resumen por Estado")
        st.dataframe(
            datos_mapa_limpio.sort_values("Volt_Minimo", ascending=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado_Normalizado": "Estado",
                "Volt_Minimo": st.column_config.NumberColumn(
                    "Volt Mínimo",
                    format="$%.2f"
                ),
                "Num_Tiendas": "Tiendas"
            }
        )

    # ==================== DIAGNÓSTICO (oculto por defecto) ====================
    with st.expander("🔍 Diagnóstico"):
        st.write(f"**Total de estados en el mapa:** {len(datos_mapa_limpio)}")
        st.write(f"**Estados no mapeados:** {set(datos_mapa['Estado']) - set(datos_mapa_limpio['Estado_Normalizado'])}")

else:
    st.error("❌ No se pudo cargar el mapa. Verifica que mexico.json esté en tu repositorio.")
    if geojson is None:
        st.info("💡 El archivo mexico.json no se encontró o no es válido.")
    if datos_mapa_limpio.empty:
        st.info("💡 No hay datos para mostrar. Verifica el archivo CSV.")
