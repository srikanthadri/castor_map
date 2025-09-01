
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

# Load shapefile
shapefile_path = "castor_village_level_acreage_ha.shp"
gdf = gpd.read_file(shapefile_path)

st.title("BANAS KANTHA District Castor Crop acereage Dashboard")

# Sidebar filters
tehsils = ["All"] + sorted(gdf["TEHSIL"].dropna().unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

if selected_tehsil == "All":
    villages = ["All"] + sorted(gdf["VILLAGE"].dropna().unique().tolist())
    filtered_gdf = gdf
else:
    villages = ["All"] + sorted(
        gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].dropna().unique().tolist()
    )
    filtered_gdf = gdf[gdf["TEHSIL"] == selected_tehsil]

selected_village = st.sidebar.selectbox("Select Village", villages)

# Legend colormap
colormap = cm.linear.YlGnBu_09.scale(
    gdf["castor_ha"].min(), gdf["castor_ha"].max()
)
colormap.caption = "Castor Area (ha)"

# Base map centered on district
m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=9)

# Plot all polygons with choropleth style
for _, row in filtered_gdf.iterrows():
    folium.GeoJson(
        row["geometry"],
        style_function=lambda feature, value=row["castor_ha"]: {
            "fillColor": colormap(value) if value is not None else "gray",
            "color": "black",
            "weight": 0.8,
            "fillOpacity": 0.6,
        },
        tooltip=folium.Tooltip(
            f"Village: {row['VILLAGE']}<br>Tehsil: {row['TEHSIL']}<br>Castor (ha): {row['castor_ha']}"
        ),
    ).add_to(m)

# Highlight selected village
if selected_village != "All":
    village_gdf = filtered_gdf[filtered_gdf["VILLAGE"] == selected_village]
    if not village_gdf.empty:
        folium.GeoJson(
            village_gdf.geometry,
            style_function=lambda x: {
                "fillColor": "red",
                "color": "red",
                "weight": 3,
                "fillOpacity": 0.4,
            },
            tooltip=folium.Tooltip(
                f"<b>Village:</b> {selected_village}<br>"
                f"<b>Castor Area:</b> {village_gdf['castor_ha'].values[0]} ha<br>"
                
            ),
        ).add_to(m)

        # Zoom to selected village
        bounds = village_gdf.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # Sidebar info panel
        st.sidebar.markdown("### Village Information")
        st.sidebar.write(f"**Village:** {selected_village}")
        st.sidebar.write(f"**Tehsil:** {selected_tehsil}")
        st.sidebar.write(f"**Castor Area (ha):** {village_gdf['castor_ha'].values[0]}")
        

# Add legend
colormap.add_to(m)

# Show map
st_folium(m, width=800, height=600)




