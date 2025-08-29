import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Load shapefile
@st.cache_data
def load_data():
    gdf = gpd.read_file("D:\\castor_map\\shp\\castor_village_level_acreage_ha.shp")
    return gdf

gdf = load_data()

st.title("Village Castor Acreage Dashboard")

# Dropdowns
districts = sorted(gdf["DISTRICT"].unique())
district = st.selectbox("Select District", districts)

tehsils = sorted(gdf[gdf["DISTRICT"] == district]["TEHSIL"].unique())
tehsil = st.selectbox("Select Tehsil", tehsils)

villages = gdf[(gdf["DISTRICT"] == district) & (gdf["TEHSIL"] == tehsil)]
village = st.selectbox("Select Village", sorted(villages["VILLAGE"].unique()))

# Show castor area (instead of 'Area')
selected = villages[villages["VILLAGE"] == village]
castor_area = selected.iloc[0]["castor_ha"]
st.metric("Castor Area (hectares)", f"{castor_area:.2f}")

# Map
m = folium.Map(location=[
    selected.geometry.centroid.y.values[0],
    selected.geometry.centroid.x.values[0]
], zoom_start=12)

folium.GeoJson(selected, tooltip=["VILLAGE", "TEHSIL", "DISTRICT", "castor_ha"]).add_to(m)

st_folium(m, width=700, height=500)
