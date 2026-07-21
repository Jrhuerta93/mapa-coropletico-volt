import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Volt Mínimo por Estado", layout="wide")
st.title("🗺️ Mapa: Volt Mínimo por Estado")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos_tiendas.csv", encoding='latin1')
    df.columns = df.columns.str.strip()
    df['VOLT'] = pd.to_numeric(df['VOLT'], errors='coerce').fillna(0.0)
    return df

df = cargar_datos()

df_estado = df.groupby('ESTADO').agg(
    Volt_minimo=('VOLT', 'min'),
    Tiendas=('Folio Emetrix', 'count')
).reset_index()

# Crear mapa simplificado con Scattergeo
fig = go.Figure(data=go.Choropleth(
    locations=df_estado['ESTADO'],
    z=df_estado['Volt_minimo'],
    locationmode="country names",
    colorscale="Blues",
    colorbar_title="Volt Mínimo ($)",
    text=df_estado['Tiendas'],
    hovertemplate='<b>%{location}</b><br>Volt Mínimo: $%{z:.2f}<br>Tiendas: %{text}<extra></extra>'
))

fig.update_layout(
    title='Distribución de Precio Volt Mínimo',
    geo_scope='north america',
    geo=dict(
        center=dict(lat=23.6345, lon=-102.5528),
        projection_scale=3.5,
        showcountries=True,
        countrycolor="Black",
        showsubstates=True,
        substatecolor="Gray"
    )
)

st.plotly_chart(fig, use_container_width=True)
