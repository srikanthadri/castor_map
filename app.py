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
m = folium.Map(
    location=[filtered_gdf.geometry.centroid.y.mean(),
              filtered_gdf.geometry.centroid.x.mean()],
    zoom_start=9,
    tiles="CartoDB positron"
)

# Color scale based on "castor_ha"
min_val, max_val = filtered_gdf["castor_ha"].min(), filtered_gdf["castor_ha"].max()
colormap = cm.LinearColormap(colors=['yellow', 'darkgreen'],
                             vmin=min_val, vmax=max_val)
colormap.caption = f"Castor Area (ha) | Min: {min_val} | Max: {max_val}"
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

tooltip = GeoJsonTooltip(
    fields=["VILLAGE", "TEHSIL", "castor_ha"],
    aliases=["Village:", "Tehsil:", "Castor (ha):"],
    localize=True
)

geojson = folium.GeoJson(
    filtered_gdf,
    style_function=style_function,
    tooltip=tooltip,
    name="Villages"
).add_to(m)

# ----------------------------
# Show map in Streamlit
# ----------------------------
st_data = st_folium(m, width=800, height=600)

# ----------------------------
# Show village info
# ----------------------------
village_info = None

# If user clicks polygon
if st_data and "last_active_drawing" in st_data and st_data["last_active_drawing"]:
    props = st_data["last_active_drawing"]["properties"]
    village_info = {
        "Village": props.get("VILLAGE"),
        "Tehsil": props.get("TEHSIL"),
        "Castor Area (ha)": props.get("castor_ha")
    }

# If village selected from dropdown
elif selected_village != "All":
    selected_row = filtered_gdf[filtered_gdf["VILLAGE"] == selected_village]
    if not selected_row.empty:
        village_info = {
            "Village": selected_row["VILLAGE"].values[0],
            "Tehsil": selected_row["TEHSIL"].values[0],
            "Castor Area (ha)": selected_row["castor_ha"].values[0]
        }

# Display info in sidebar
if village_info:
    st.sidebar.subheader("Village Information")
    for k, v in village_info.items():
        st.sidebar.write(f"**{k}:** {v}")

# ----------------------------
# Download CSV button
# ----------------------------
csv_data = gdf[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].copy()
csv = csv_data.to_csv(index=False)

st.sidebar.download_button(
    label="📥 Download District Data (CSV)",
    data=csv,
    file_name="banaskantha_castor_acreage.csv",
    mime="text/csv"
)
