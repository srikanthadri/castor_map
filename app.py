import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# ---- Load shapefile ----
shapefile_path = r"castor_village_level_acreage_ha.shp"
gdf = gpd.read_file(shapefile_path)

st.title("Village Dashboard - Castor Crop Area")

# ---- Dropdown for Tehsil ----
tehsil_list = gdf["TEHSIL"].unique()
selected_tehsil = st.selectbox("Select Tehsil", tehsil_list)

# ---- Filter villages by Tehsil ----
villages_in_tehsil = gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].unique()
selected_village = st.selectbox("Select Village", villages_in_tehsil)

# ---- Get castor area for selected village ----
village_data = gdf[(gdf["TEHSIL"] == selected_tehsil) & (gdf["VILLAGE"] == selected_village)]
castor_area = village_data["castor_ha"].values[0]

st.metric(label="Castor Area (ha)", value=castor_area)

# ---- Plot shapefile on map ----
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # India center

# Add full Tehsil boundary
folium.GeoJson(
    village_data.geometry,
    name="Village Boundary",
    tooltip=f"{selected_village} - {castor_area} ha"
).add_to(m)

# Show map
st_folium(m, width=700, height=500)
