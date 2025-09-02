import os
import glob
from pathlib import Path

import streamlit as st
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# ----------------------------
# Helpers for paths & caching
# ----------------------------
def shapefile_mtime_key(shp_path: str) -> float:
    """Cache key based on the newest modified time among shapefile components."""
    stem = os.path.splitext(shp_path)[0]
    sidecars = glob.glob(stem + ".*")
    if not sidecars:
        return 0.0
    return max(os.path.getmtime(f) for f in sidecars)

# ----------------------------
# Load polygon shapefile
# ----------------------------
@st.cache_data
def load_polygons():
    gdf = gpd.read_file(r"shp/polygons.shp")  # 👈 update with your shapefile
    gdf = gdf.to_crs(epsg=4326)

    # Calculate acreage (ensure projected first)
    gdf_m = gdf.to_crs(epsg=3857)
    gdf["acreage"] = gdf_m.area / 4046.86  # sqm → acres

    # Assign category
    gdf["Category"] = gdf["id"].apply(lambda x: "Existed" if x > 10 else "Suggested")
    return gdf

# ============================
# App
# ============================
st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

# Load polygons
gdf = load_polygons()

# ============================
# Map
# ============================
# Map center
map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

# Colors
color_map = {"Existed": "lightblue", "Suggested": "lightgreen"}

# Style function
def style_function(feature):
    cat = feature["properties"].get("Category")
    return {
        "fillColor": color_map.get(cat, "grey"),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.6,
    }

# Tooltip with acreage
tooltip = GeoJsonTooltip(
    fields=["id", "Category", "acreage"],
    aliases=["Polygon ID:", "Type:", "Acreage (ac):"],
    localize=True,
    sticky=True,
)

folium.GeoJson(
    gdf,
    style_function=style_function,
    tooltip=tooltip,
    name="Polygons",
).add_to(m)

# ============================
# Map -> Streamlit
# ============================
st_data = st_folium(m, width=1000, height=650)

# ============================
# Download CSV
# ============================
csv_data = gdf[["id", "Category", "acreage"]].copy()
st.sidebar.download_button(
    "📥 Download Polygons Data (CSV)",
    data=csv_data.to_csv(index=False),
    file_name="banaskantha_polygons.csv",
    mime="text/csv",
)
