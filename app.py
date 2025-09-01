
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors

# Load shapefile
shapefile_path = r"castor_village_level_acreage_ha.shp"
gdf = gpd.read_file(shapefile_path)

# Sidebar filters
tehsils = gdf["TEHSIL"].unique()
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

villages = gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].unique()
selected_village = st.sidebar.selectbox("Select Village", villages)

# Filter data
tehsil_gdf = gdf[gdf["TEHSIL"] == selected_tehsil]
village_gdf = tehsil_gdf[tehsil_gdf["VILLAGE"] == selected_village]

# Create folium map centered on the tehsil
tehsil_center = tehsil_gdf.geometry.centroid.unary_union.centroid
m = folium.Map(location=[tehsil_center.y, tehsil_center.x], zoom_start=11)

# Color scale for castor_ha
min_ha, max_ha = tehsil_gdf["castor_ha"].min(), tehsil_gdf["castor_ha"].max()
colormap = cm.ScalarMappable(norm=colors.Normalize(vmin=min_ha, vmax=max_ha), cmap="YlGnBu")

def style_function(feature):
    ha_value = feature["properties"]["castor_ha"]
    return {
        "fillColor": colors.to_hex(colormap.to_rgba(ha_value)),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.6,
    }

# Add all villages in selected tehsil with color based on ha
folium.GeoJson(
    tehsil_gdf,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["VILLAGE", "castor_ha"]),
).add_to(m)

# Highlight selected village
folium.GeoJson(
    village_gdf,
    style_function=lambda x: {
        "fillColor": "red",
        "color": "red",
        "weight": 3,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["VILLAGE", "castor_ha"]),
).add_to(m)

# Add legend
colormap = cm.ScalarMappable(norm=colors.Normalize(vmin=min_ha, vmax=max_ha), cmap="YlGnBu")
colormap._A = []
m.get_root().html.add_child(folium.Element(colormap.to_html()))

# Show map in Streamlit
st_folium(m, width=700, height=500)

