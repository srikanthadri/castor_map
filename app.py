import streamlit as st
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import branca.colormap as cm

# ----------------------------
# Load shapefiles
# ----------------------------
@st.cache_data
def load_data():
    gdf = gpd.read_file(r"shp//castor_village_level_acreage_ha_new_int.shp")
    gdf = gdf.to_crs(epsg=4326)
    return gdf

@st.cache_data
def load_points():
    points = gpd.read_file(r"shp//points_suggested.shp")  # point shapefile
    points = points.to_crs(epsg=4326)
    return points

gdf = load_data()
points_gdf = load_points()

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

# Village filter
if selected_tehsil != "All":
    villages = gdf[gdf["TEHSIL"] == selected_tehsil]["VILLAGE"].dropna().unique().tolist()
else:
    villages = gdf["VILLAGE"].dropna().unique().tolist()

villages = ["All"] + sorted(villages)
selected_village = st.sidebar.selectbox("Select Village", villages)

# Point filter (suggested locations)
point_names = points_gdf["NAME"].tolist() if "NAME" in points_gdf.columns else [f"Point {i}" for i in range(len(points_gdf))]
point_selection = st.sidebar.selectbox("Select Suggested Location", ["None"] + point_names)

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
colormap = cm.LinearColormap(colors=['yellow', 'darkgreen'], vmin=min_val, vmax=max_val)
colormap.caption = f"Castor Area (ha) | Min: {min_val} | Max: {max_val}"
colormap.add_to(m)

# ----------------------------
# Add polygons (villages)
# ----------------------------
def style_function(feature):
    village_name = feature["properties"]["VILLAGE"]
    ha_value = feature["properties"]["castor_ha"]

    if selected_village != "All" and village_name == selected_village:
        return {"fillColor": "blue", "color": "black", "weight": 3, "fillOpacity": 0.8}
    else:
        return {"fillColor": colormap(ha_value) if ha_value is not None else "grey",
                "color": "black", "weight": 1, "fillOpacity": 0.6}

tooltip = GeoJsonTooltip(fields=["VILLAGE", "TEHSIL", "castor_ha"],
                         aliases=["Village:", "Tehsil:", "Castor (ha):"], localize=True)

folium.GeoJson(filtered_gdf, style_function=style_function, tooltip=tooltip, name="Villages").add_to(m)

# ----------------------------
# Add suggested locations (points)
# ----------------------------
for _, row in points_gdf.iterrows():
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=row["NAME"] if "NAME" in row else "Suggested Location",
        icon=folium.Icon(color="red", icon="map-marker")
    ).add_to(m)

# ----------------------------
# Highlight villages within 25 km of selected point
# ----------------------------
buffered_villages = None
if point_selection != "None":
    selected_point = points_gdf[points_gdf["NAME"] == point_selection] if "NAME" in points_gdf.columns else points_gdf.iloc[[point_names.index(point_selection)-1]]

    # Reproject to meters for buffer
    point_m = selected_point.to_crs(epsg=3857)
    buffer_m = point_m.buffer(25000)  # 25 km
    buffer = buffer_m.to_crs(epsg=4326)

    # Get villages within buffer
    buffered_villages = gdf[gdf.intersects(buffer.iloc[0])]

    # Add buffer to map
    folium.GeoJson(buffer, style_function=lambda x: {"fillColor": "none", "color": "red", "weight": 2}).add_to(m)

    # Highlight villages in buffer
    folium.GeoJson(buffered_villages,
                   style_function=lambda x: {"fillColor": "orange", "color": "black", "weight": 2, "fillOpacity": 0.7},
                   tooltip=tooltip).add_to(m)

# ----------------------------
# Show map
# ----------------------------
st_data = st_folium(m, width=800, height=600)

# ----------------------------
# Show village info
# ----------------------------
village_info = None
if st_data and "last_active_drawing" in st_data and st_data["last_active_drawing"]:
    props = st_data["last_active_drawing"]["properties"]
    village_info = {"Village": props.get("VILLAGE"), "Tehsil": props.get("TEHSIL"), "Castor Area (ha)": props.get("castor_ha")}
elif selected_village != "All":
    selected_row = filtered_gdf[filtered_gdf["VILLAGE"] == selected_village]
    if not selected_row.empty:
        village_info = {"Village": selected_row["VILLAGE"].values[0], "Tehsil": selected_row["TEHSIL"].values[0], "Castor Area (ha)": selected_row["castor_ha"].values[0]}

if village_info:
    st.sidebar.subheader("Village Information")
    for k, v in village_info.items():
        st.sidebar.write(f"**{k}:** {v}")

# ----------------------------
# Download CSV
# ----------------------------
csv_data = gdf[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].copy()
csv = csv_data.to_csv(index=False)

st.sidebar.download_button("📥 Download District Data (CSV)", data=csv, file_name="banaskantha_castor_acreage.csv", mime="text/csv")

# If buffer villages selected, allow download
if buffered_villages is not None and not buffered_villages.empty:
    csv_buf = buffered_villages[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].to_csv(index=False)
    st.sidebar.download_button("📥 Download Villages in 25 km Buffer (CSV)", data=csv_buf, file_name="villages_in_buffer.csv", mime="text/csv")
