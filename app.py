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
def shapefile_mtime_key(shp_path: str) -> float:
    """Cache key based on the newest modified time among all companion files of a shapefile."""
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
# Load location polygons
# ----------------------------
@st.cache_data
def load_location_polygons():
    gdf_loc = gpd.read_file("shp/polygons.shp")  # <-- your shapefile
    gdf_loc = gdf_loc.to_crs(epsg=4326)
    return gdf_loc


# ============================
# App
# ============================
st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

# Load data
gdf = load_villages()
loc_gdf = load_location_polygons()

# ============================
# Sidebar filters
# ============================
st.sidebar.title("Filters")

# Tehsil filter
tehsils = ["All"] + sorted(gdf["TEHSIL"].dropna().unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils, index=0)

# Village filter
if selected_tehsil != "All":
    villages = gdf.loc[gdf["TEHSIL"] == selected_tehsil, "VILLAGE"].dropna().unique().tolist()
else:
    villages = gdf["VILLAGE"].dropna().unique().tolist()
villages = ["All"] + sorted(villages)
selected_village = st.sidebar.selectbox("Select Village", villages, index=0)

# Polygon filter
# Ensure IDs are integers
all_ids = sorted([int(i) for i in loc_gdf["id"].unique().tolist()])

# Sidebar selection (keep "All" as string, rest as ints)
selected_raw = st.sidebar.multiselect(
    "Select Location IDs", ["All"] + all_ids, default="All"
)

# Normalize selection
if "All" in selected_raw:
    selected_ids = all_ids
else:
    selected_ids = [int(i) for i in selected_raw]

# Filter polygons
filtered_polygons = loc_gdf[loc_gdf["id"].isin(selected_ids)]


# ============================
# Data filtering
# ============================
filtered_gdf = gdf
if selected_tehsil != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["TEHSIL"] == selected_tehsil]

# Filter villages that fall inside selected polygons
if not filtered_polygons.empty and "All" not in selected_ids:
    # Keep villages that intersect polygons (touch or overlap)
    filtered_gdf = gpd.sjoin(filtered_gdf, filtered_polygons, predicate="intersects")
# ============================
# Map
# ============================
if filtered_gdf.empty:
    map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
else:
    map_center = [filtered_gdf.geometry.centroid.y.mean(), filtered_gdf.geometry.centroid.x.mean()]

m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

# Color scale for castor_ha
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
# Location polygons overlay (filtered)
# ============================
def style_location(feature, color):
    return {
        "fillColor": color,
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.5,
    }

existing_gdf = filtered_polygons[filtered_polygons["id"] > 10]
suggested_gdf = filtered_polygons[filtered_polygons["id"] <= 10]

# Existing locations (green)
folium.GeoJson(
    existing_gdf,
    style_function=lambda x: style_location(x, "green"),
    tooltip=GeoJsonTooltip(
        fields=["id", "acreage"],
        aliases=["Location ID:", "Acreage (ha):"],
        localize=True,
    ),
    name="Existing Locations",
).add_to(m)

# Suggested locations (red)
folium.GeoJson(
    suggested_gdf,
    style_function=lambda x: style_location(x, "red"),
    tooltip=GeoJsonTooltip(
        fields=["id", "acreage"],
        aliases=["Location ID:", "Acreage (ha):"],
        localize=True,
    ),
    name="Suggested Locations",
).add_to(m)

# Add acreage labels for filtered polygons
for _, row in filtered_polygons.iterrows():
    centroid = row.geometry.centroid
    folium.Marker(
        location=[centroid.y, centroid.x],
        icon=folium.DivIcon(
            html=f"""<div style="font-size:12px; color:black; text-align:center;">
                     {row['acreage']} ha</div>"""
        ),
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

# ============================
# Download CSV per polygon
# ============================
ids_to_export = selected_ids

for pid in ids_to_export:
    poly = loc_gdf[loc_gdf["id"] == pid]
    # Use intersects instead of within
    villages_inside = gpd.sjoin(gdf, poly, predicate="intersects")
    if not villages_inside.empty:
        export_df = villages_inside[["VILLAGE", "TEHSIL", "castor_ha"]].copy()
        st.sidebar.download_button(
            f"📥 Download Villages (Polygon {pid})",
            data=export_df.to_csv(index=False),
            file_name=f"polygon_{pid}_villages.csv",
            mime="text/csv",
        )

