import streamlit as st
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import branca.colormap as cm

# ----------------------------
# Load shapefile
# ----------------------------
@st.cache_data
def load_data():
    gdf = gpd.read_file(r"castor_village_level_acreage_ha.shp")  # change path
    gdf = gdf.to_crs(epsg=4326)  # convert to lat/lon
    return gdf

gdf = load_data()

# ----------------------------
# Title
# ----------------------------
st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.title("Filters")

# Tehsil filter
tehsils = ["All"] + sorted(gdf["TEHSIL"].dropna().unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

# Filter villages based on tehsil
if selected_tehsil != "All":
    villages = gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].dropna().unique().tolist()
else:
    villages = gdf["VILLAGE"].dropna().unique().tolist()

villages = ["All"] + sorted(villages)
selected_village = st.sidebar.selectbox("Select Village", villages)

# ----------------------------
# Data filtering
# ----------------------------
filtered_gdf = gdf.copy()

if selected_tehsil != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["TEHSIL"] == selected_tehsil]

# ----------------------------
# Create map
# ----------------------------
m = folium.Map(location=[filtered_gdf.geometry.centroid.y.mean(),
                         filtered_gdf.geometry.centroid.x.mean()],
               zoom_start=9, tiles="CartoDB positron")

# Color scale based on "castor_ha"
min_val, max_val = filtered_gdf["castor_ha"].min(), filtered_gdf["castor_ha"].max()
colormap = cm.LinearColormap(colors=['yellow', 'darkgreen'],
                             vmin=min_val, vmax=max_val)
colormap.caption = "Castor Area (ha)"
colormap.add_to(m)

# Add polygons
def style_function(feature):
    village_name = feature["properties"]["VILLAGE"]
    ha_value = feature["properties"]["castor_ha"]

    # Highlight if selected
    if selected_village != "All" and village_name == selected_village:
        return {
            "fillColor": "blue",
            "color": "black",
            "weight": 3,
            "fillOpacity": 0.8,
        }
    else:
        return {
            "fillColor": colormap(ha_value) if ha_value is not None else "grey",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        }

tooltip = GeoJsonTooltip(fields=["VILLAGE", "TEHSIL", "castor_ha"],
                         aliases=["Village:", "Tehsil:", "Castor (ha):"],
                         localize=True)

folium.GeoJson(
    filtered_gdf,
    style_function=style_function,
    tooltip=tooltip,
).add_to(m)

# ----------------------------
# Show map
# ----------------------------
st_data = st_folium(m,
