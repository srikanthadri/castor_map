import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

# --------------------
# Load shapefile
# --------------------
@st.cache_data
def load_data():
    gdf = gpd.read_file("castor_village_level_acreage_ha.shp")
    gdf = gdf.to_crs(epsg=4326)  # ensure lat/lon
    return gdf

gdf = load_data()

# Ensure HA column is numeric
gdf["HA"] = gdf["HA"].fillna(0).astype(float)

# --------------------
# Sidebar filters
# --------------------
st.sidebar.header("Filters")

tehsils = ["All"] + sorted(gdf["tehsil"].dropna().unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

villages = ["All"]
if selected_tehsil != "All":
    villages += sorted(gdf[gdf["tehsil"] == selected_tehsil]["village"].dropna().unique().tolist())
else:
    villages += sorted(gdf["village"].dropna().unique().tolist())

selected_village = st.sidebar.selectbox("Select Village", villages)

# --------------------
# Filter GeoDataFrame
# --------------------
if selected_tehsil == "All":
    filtered_gdf = gdf.copy()
else:
    filtered_gdf = gdf[gdf["tehsil"] == selected_tehsil]

if selected_village != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["village"] == selected_village]

# --------------------
# Create Folium Map
# --------------------
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
m = folium.Map(location=center, zoom_start=9, tiles="cartodbpositron")

# Color scale
min_val, max_val = gdf["HA"].min(), gdf["HA"].max()
colormap = cm.linear.YlGnBu_09.scale(min_val, max_val)
colormap.caption = f"Castor Area (ha)\nMin: {min_val:.1f} | Max: {max_val:.1f}"
colormap.add_to(m)

# Add all villages with HA coloring
style_function = lambda x: {
    "fillColor": colormap(x["properties"]["HA"]),
    "color": "black",
    "weight": 0.5,
    "fillOpacity": 0.7,
}

highlight_function = lambda x: {
    "fillColor": "#ff0000",
    "color": "red",
    "weight": 2,
    "fillOpacity": 0.9,
}

folium.GeoJson(
    gdf,
    name="All Villages",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(fields=["tehsil", "village", "HA"], aliases=["Tehsil", "Village", "HA (ha)"]),
).add_to(m)

# Zoom & highlight selected village
selected_info = None
if selected_village != "All":
    sel = gdf[gdf["village"] == selected_village]
    if not sel.empty:
        folium.GeoJson(
            sel,
            style_function=lambda x: {"fillColor": "#ff0000", "color": "red", "weight": 3, "fillOpacity": 0.9},
            tooltip=folium.GeoJsonTooltip(fields=["tehsil", "village", "HA"]),
        ).add_to(m)
        centroid = sel.geometry.centroid.iloc[0]
        m.location = [centroid.y, centroid.x]
        m.zoom_start = 12
        selected_info = sel.iloc[0].to_dict()

# --------------------
# Render map
# --------------------
st_data = st_folium(m, width=900, height=600)

# --------------------
# Click selection
# --------------------
if st_data and st_data.get("last_active_drawing"):
    props = st_data["last_active_drawing"]["properties"]
    selected_info = props

# --------------------
# Info Panel
# --------------------
st.sidebar.header("Village Info")
if selected_info:
    st.sidebar.write(f"**Tehsil:** {selected_info['tehsil']}")
    st.sidebar.write(f"**Village:** {selected_info['village']}")
    st.sidebar.write(f"**Area (ha):** {selected_info['HA']:.2f}")
else:
    st.sidebar.write("Select a village from dropdown or click on map.")
