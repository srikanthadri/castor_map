
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import branca.colormap as bcm

# Load shapefile
shapefile_path = r"castor_village_level_acreage_ha.shp"
gdf = gpd.read_file(shapefile_path)

# Reproject to web mercator for centroid calculations
gdf = gdf.to_crs(epsg=3857)

# Sidebar filters
tehsils = gdf["TEHSIL"].unique()
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

villages = gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].unique()
selected_village = st.sidebar.selectbox("Select Village", villages)

# Filter data
tehsil_gdf = gdf[gdf["TEHSIL"] == selected_tehsil]
village_gdf = tehsil_gdf[tehsil_gdf["VILLAGE"] == selected_village]

# Compute center of tehsil for map zoom
tehsil_center = tehsil_gdf.geometry.centroid.unary_union.centroid
# Convert back to lat/lon for folium
tehsil_center = gpd.GeoSeries([tehsil_center], crs=3857).to_crs(epsg=4326).iloc[0]

m = folium.Map(location=[tehsil_center.y, tehsil_center.x], zoom_start=11)

# Color scale for castor_ha
min_ha, max_ha = tehsil_gdf["castor_ha"].min(), tehsil_gdf["castor_ha"].max()
colormap = bcm.linear.YlGnBu_09.scale(min_ha, max_ha)
colormap.caption = "Castor Area (ha)"

def style_function(feature):
    ha_value = feature["properties"]["castor_ha"]
    return {
        "fillColor": colormap(ha_value),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.6,
    }

# Add all villages in selected tehsil
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
colormap.add_to(m)

# Show map in Streamlit
st_folium(m, width=700, height=500)


