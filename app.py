
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors

# Load shapefile
gdf = gpd.read_file(r"castor_village_level_acreage_ha.shp")

# Sidebar filters
selected_tehsil = st.sidebar.selectbox("Select Tehsil", gdf["TEHSIL"].unique())
tehsil_data = gdf[gdf["TEHSIL"] == selected_tehsil]

selected_village = st.sidebar.selectbox("Select Village", tehsil_data["VILLAGE"].unique())
village_data = tehsil_data[tehsil_data["VILLAGE"] == selected_village]

# Create folium map centered on tehsil
m = folium.Map(location=[tehsil_data.geometry.centroid.y.mean(), 
                         tehsil_data.geometry.centroid.x.mean()], zoom_start=11)

# Color mapping for villages (based on castor_ha)
norm = colors.Normalize(vmin=tehsil_data["castor_ha"].min(), vmax=tehsil_data["castor_ha"].max())
cmap = cm.ScalarMappable(norm=norm, cmap="YlGn")

for _, row in tehsil_data.iterrows():
    color = colors.to_hex(cmap.to_rgba(row["castor_ha"]))
    folium.GeoJson(
        row["geometry"],
        style_function=lambda feature, color=color: {
            "fillColor": color,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        tooltip=f"{row['VILLAGE']} - {row['castor_ha']} ha"
    ).add_to(m)

# Highlight selected village
folium.GeoJson(
    village_data["geometry"],
    style_function=lambda feature: {
        "fillColor": "red",
        "color": "red",
        "weight": 3,
        "fillOpacity": 0.8,
    },
    tooltip=f"Selected: {selected_village} - {village_data['castor_ha'].values[0]} ha"
).add_to(m)

# Show map
st_folium(m, width=700, height=500)


# Show map in Streamlit
st_folium(m, width=700, height=500)


