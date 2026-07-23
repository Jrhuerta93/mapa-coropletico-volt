# ============================================
# TAB 1: MAPA DE PRECIOS (CORREGIDO)
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
    # Crear una lista de strings para el hover
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
        
        # ============================================
        # AGREGAR MAPA CON HOVER CORRECTO
        # ============================================
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
            # CORREGIDO: usar customdata para el hover
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
