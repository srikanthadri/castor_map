import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors

# -----------------------
# Streamlit Page Config
# -----------------------
st.set_page_config(layout="wide")
st.title("🗺️ Castor Acreage Dashboard")

# -----------------------
# Load Shapefile
# -----------------------
gdf = gpd.read_file(r"castor_village_level_acreage_ha.shp")

# -----------------------
# Sidebar Filters
# -----------------------
tehsil_options = ["All"] + sorted(gdf["TEHSIL"].unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsil_options)

if selected_tehsil == "All":
    tehsil_data = gdf.copy()
else:
    tehsil_data = gdf[gdf["TEHSIL"] == selected_tehsil]

# Village filter (only if a tehsil is selected)
selected_village = None
if selected_tehsil != "All":
    selected_village = st.sidebar.selectbox("Select Village", tehsil_data["VILLAGE"].unique())
    village_data = tehsil_data[tehsil_data["VILLAGE"] == selected_village]

# -----------------------
# Create Folium Map
# -----------------------
# Center map: all India or zoom to tehsil
if selected_tehsil == "All":
    map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    zoom_level = 6
else:
    map_center = [tehsil_data.geometry.centroid.y.mean(), tehsil_data.geometry.centroid.x.mean()]
    zoom_level = 11

m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="cartodbpositron")

# -----------------------
# Color Mapping by castor_ha
# -----------------------
norm = colors.Normalize(vmin=gdf["castor_ha"].min(), vmax=gdf["castor_ha"].max())
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
        tooltip=folium.Tooltip(
            f"<b>Village:</b> {row['VILLAGE']}<br>"
            f"<b>Tehsil:</b> {row['TEHSIL']}<br>"
            f"<b>District:</b> {row['DISTRICT']}<br>"
            f"<b>Castor Area:</b> {row['castor_ha']} ha"
        )
    ).add_to(m)

# -----------------------
# Highlight Selected Village
# -----------------------
if selected_tehsil != "All" and selected_village:
    folium.GeoJson(
        village_data["geometry"],
        style_function=lambda feature: {
            "fillColor": "red",
            "color": "red",
            "weight": 3,
            "fillOpacity": 0.8,
        },
        tooltip=f"🌟 Selected: {selected_village} - {village_data['castor_ha'].values[0]} ha"
    ).add_to(m)

# -----------------------
# Show Map
# -----------------------
st_folium(m, width=1000, height=600)
