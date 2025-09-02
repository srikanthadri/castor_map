import os
import glob
from pathlib import Path

import streamlit as st
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import branca.colormap as cm

st.set_page_config(layout="wide")

# ----------------------------
# Helpers for paths & caching
# ----------------------------
def find_points_path():
    """Try common paths for the points shapefile; return first that exists."""
    candidates = [
        "shp/points_suggested.shp",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None

def shapefile_mtime_key(shp_path: str) -> float:
    """
    Cache key based on the newest modified time among all companion files
    of a shapefile (e.g., .shp, .dbf, .shx, .prj).
    """
    stem = os.path.splitext(shp_path)[0]
    sidecars = glob.glob(stem + ".*")
    if not sidecars:
        return 0.0
    return max(os.path.getmtime(f) for f in sidecars)

# ----------------------------
# Load polygon shapefile (villages)
# ----------------------------
@st.cache_data
def load_villages():
    gdf = gpd.read_file(r"shp/castor_village_level_acreage_ha_new_int.shp")
    gdf = gdf.to_crs(epsg=4326)
    return gdf

# ----------------------------
# Load points shapefile (suggested locations)
# Cache depends on file mtime so new commits are picked up
# ----------------------------
@st.cache_data
def load_points(points_path: str, version_key: float):
    points = gpd.read_file(points_path)
    points = points.to_crs(epsg=4326)
    return points

# ----------------------------
# Create buffers around points (25 km)
# ----------------------------
@st.cache_data
def create_buffers(_points_gdf, distance_km: float = 25.0, version_key: float = 0.0):
    # buffer in meters in a projected CRS, then back to 4326
    pts_3857 = _points_gdf.to_crs(epsg=3857)
    buf_series = pts_3857.buffer(distance_km * 1000.0)
    buf_gdf = gpd.GeoDataFrame(
        _points_gdf.drop(columns="geometry"),
        geometry=buf_series,
        crs=pts_3857.crs,
    ).to_crs(epsg=4326)
    return buf_gdf

# ============================
# App
# ============================
st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

# Load villages
gdf = load_villages()

# ============================
# Sidebar filters
# ============================
st.sidebar.title("Filters")

# Tehsil filter
tehsils = ["All"] + sorted(gdf["TEHSIL"].dropna().unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils, index=0)

# Village filter based on tehsil
if selected_tehsil != "All":
    villages = gdf.loc[gdf["TEHSIL"] == selected_tehsil, "VILLAGE"].dropna().unique().tolist()
else:
    villages = gdf["VILLAGE"].dropna().unique().tolist()
villages = ["All"] + sorted(villages)
selected_village = st.sidebar.selectbox("Select Village", villages, index=0)

# Suggested locations toggles
st.sidebar.markdown("---")
st.sidebar.subheader("Suggested Locations")
show_points = st.sidebar.checkbox("Show Suggested Points", value=True)
show_buffers = st.sidebar.checkbox("Show 25 km Buffers", value=True)

# Optional refresh to bust all caches manually
if st.sidebar.button("🔄 Refresh Data (clear cache)"):
    st.cache_data.clear()
    st.experimental_rerun()

# ============================
# Data filtering
# ============================
filtered_gdf = gdf
if selected_tehsil != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["TEHSIL"] == selected_tehsil]

# ============================
# Map
# ============================
# Fallback center if filter empties data
if filtered_gdf.empty:
    map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
else:
    map_center = [filtered_gdf.geometry.centroid.y.mean(), filtered_gdf.geometry.centroid.x.mean()]

m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

# Color scale based on castor_ha
ha_series = filtered_gdf["castor_ha"].dropna()
if ha_series.empty:
    min_val, max_val = 0, 1
else:
    min_val, max_val = float(ha_series.min()), float(ha_series.max())

colormap = cm.LinearColormap(colors=["yellow", "darkgreen"], vmin=min_val, vmax=max_val)
colormap.caption = f"Castor Area (ha) | Min: {min_val:.2f} | Max: {max_val:.2f}"
colormap.add_to(m)

# Style function for villages
def style_function(feature):
    village_name = feature["properties"].get("VILLAGE")
    ha_value = feature["properties"].get("castor_ha")

    if selected_village != "All" and village_name == selected_village:
        return {"fillColor": "blue", "color": "black", "weight": 3, "fillOpacity": 0.8}
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
    localize=True,
)

folium.GeoJson(
    filtered_gdf,
    style_function=style_function,
    tooltip=tooltip,
    name="Villages",
).add_to(m)

# ============================
# Suggested points & buffers
# ============================
points_path = find_points_path()

if (show_points or show_buffers):
    if not points_path:
        st.sidebar.error(
            "⚠️ Suggested points shapefile not found.\n\n"
            "Expected one of:\n"
            "- shp/points_suggested.shp\n- shp/suggested_points.shp\n"
            "- points_suggested.shp\n- suggested_points.shp"
        )
    else:
        version_key = shapefile_mtime_key(points_path)
        try:
            points_gdf = load_points(points_path, version_key)
        except Exception as e:
            st.sidebar.error(f"Error loading points shapefile: {e}")
            points_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

        if not points_gdf.empty:
            # Add points
            if show_points:
                for _, row in points_gdf.iterrows():
                    name = None
                    for cand in ("NAME", "Name", "name", "LABEL"):
                        if cand in points_gdf.columns:
                            name = row.get(cand)
                            break
                    popup_txt = name if name else "Suggested Location"

                    folium.Marker(
                        location=[row.geometry.y, row.geometry.x],
                        popup=str(popup_txt),
                        icon=folium.Icon(color="red", icon="map-marker"),
                    ).add_to(m)

            # Add buffers
            if show_buffers:
                buf_gdf = create_buffers(points_gdf, distance_km=25.0, version_key=version_key)
                folium.GeoJson(
                    buf_gdf,
                    name="25 km Buffers",
                    style_function=lambda x: {
                        "color": "blue",
                        "fillColor": "lightblue",
                        "fillOpacity": 0.25,
                        "weight": 2,
                    },
                ).add_to(m)

# ============================
# Map -> Streamlit
# ============================
st_data = st_folium(m, width=1000, height=650)

# ============================
# Village info panel
# ============================
village_info = None
if st_data and "last_active_drawing" in st_data and st_data["last_active_drawing"]:
    props = st_data["last_active_drawing"]["properties"]
    village_info = {
        "Village": props.get("VILLAGE"),
        "Tehsil": props.get("TEHSIL"),
        "Castor Area (ha)": props.get("castor_ha"),
    }
elif selected_village != "All":
    sel_row = filtered_gdf[filtered_gdf["VILLAGE"] == selected_village]
    if not sel_row.empty:
        village_info = {
            "Village": sel_row["VILLAGE"].values[0],
            "Tehsil": sel_row["TEHSIL"].values[0],
            "Castor Area (ha)": sel_row["castor_ha"].values[0],
        }

if village_info:
    st.sidebar.subheader("Village Information")
    for k, v in village_info.items():
        st.sidebar.write(f"**{k}:** {v}")

# ============================
# Download CSV (district-wide)
# ============================
csv_data = gdf[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].copy()
st.sidebar.download_button(
    "📥 Download District Data (CSV)",
    data=csv_data.to_csv(index=False),
    file_name="banaskantha_castor_acreage.csv",
    mime="text/csv",
)
