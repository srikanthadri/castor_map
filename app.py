import os
import glob
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
    stem = os.path.splitext(shp_path)[0]
    sidecars = glob.glob(stem + ".*")
    if not sidecars:
        return 0.0
    return max(os.path.getmtime(f) for f in sidecars)

# ----------------------------
# Load shapefiles
# ----------------------------
@st.cache_data
def load_villages():
    gdf = gpd.read_file(r"shp/castor_village_level_acreage_ha_new_int.shp")
    gdf = gdf.to_crs(epsg=4326)
    return gdf

@st.cache_data
def load_location_polygons():
    gdf_loc = gpd.read_file("shp/polygons.shp")
    gdf_loc = gdf_loc.to_crs(epsg=4326)
    return gdf_loc

# ============================
# App title
# ============================
st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

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
all_ids = sorted([int(i) for i in loc_gdf["id"].unique().tolist()])
selected_raw = st.sidebar.multiselect("Select Suggested Location IDs", ["All"] + all_ids, default="All")
if "All" in selected_raw:
    selected_ids = all_ids
else:
    selected_ids = [int(i) for i in selected_raw]

filtered_polygons = loc_gdf[loc_gdf["id"].isin(selected_ids)]

# ============================
# Polygon Layer Toggles
# ============================
st.sidebar.subheader("Polygon Layer Controls")
show_existing = st.sidebar.checkbox("Show Existing Locations (Red)", value=True)
show_suggested = st.sidebar.checkbox("Show Suggested Locations (Green)", value=True)

# ============================
# Data filtering
# ============================
filtered_gdf = gdf.copy()
if selected_tehsil != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["TEHSIL"] == selected_tehsil]

# Villages touching polygons
if not filtered_polygons.empty and "All" not in selected_raw:
    filtered_gdf = gpd.sjoin(filtered_gdf, filtered_polygons, predicate="intersects")
    filtered_gdf = filtered_gdf.drop_duplicates(subset="VILLAGE")
    filtered_gdf = filtered_gdf.drop(columns=["index_right"], errors="ignore")

# ============================
# Map setup
# ============================
if filtered_gdf.empty:
    map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
else:
    map_center = [filtered_gdf.geometry.centroid.y.mean(), filtered_gdf.geometry.centroid.x.mean()]

m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

# Color scale for castor_ha
ha_series = filtered_gdf["castor_ha"].dropna()
min_val, max_val = (0, 1) if ha_series.empty else (float(ha_series.min()), float(ha_series.max()))
colormap = cm.LinearColormap(colors=["yellow", "darkgreen"], vmin=min_val, vmax=max_val)
colormap.caption = f"Castor Area (ha) | Min: {min_val:.2f} | Max: {max_val:.2f}"
colormap.add_to(m)

# Village style
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

if not filtered_gdf.empty:
    folium.GeoJson(
        filtered_gdf,
        style_function=style_function,
        tooltip=GeoJsonTooltip(
            fields=["VILLAGE", "TEHSIL", "castor_ha"],
            aliases=["Village:", "Tehsil:", "Castor (ha):"],
            localize=True,
        ),
        name="Villages",
    ).add_to(m)

# ============================
# Polygons overlay
# ============================
def style_location(feature, color):
    return {"fillColor": color, "color": "black", "weight": 2, "fillOpacity": 0.5}

existing_gdf = filtered_polygons[filtered_polygons["id"] > 10]
suggested_gdf = filtered_polygons[filtered_polygons["id"] <= 10]

# Existing polygons
if show_existing and not existing_gdf.empty:
    folium.GeoJson(
        existing_gdf,
        style_function=lambda x: style_location(x, "blue"),
        tooltip=GeoJsonTooltip(fields=["id", "acreage"], aliases=["Location ID:", "Acreage (ha):"]),
        name="Existing Locations",
    ).add_to(m)

# Suggested polygons
if show_suggested and not suggested_gdf.empty:
    folium.GeoJson(
        suggested_gdf,
        style_function=lambda x: style_location(x, "maroon"),
        tooltip=GeoJsonTooltip(fields=["id", "acreage"], aliases=["Location ID:", "Acreage (ha):"]),
        name="Suggested Locations",
    ).add_to(m)

# ============================
# Add centroids with small markers + labels
# ============================
for _, row in filtered_polygons.iterrows():
    centroid = row.geometry.centroid
    color = "maroon" if row["id"] <= 10 else "blue"

    if (color == "maroon" and show_suggested) or (color == "blue" and show_existing):
        # Small circle marker
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=4,  # small size
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=f"ID: {row['id']}, Acreage: {row['acreage']} ha"
        ).add_to(m)

        # Label on top (with small offset)
        folium.Marker(
            location=[centroid.y + 0.0001, centroid.x],  # tiny latitude offset
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    display: inline-block;
                    font-size: 10px; 
                    color: black; 
                    font-weight: bold; 
                    text-align: center; 
                    line-height: 1.2; 
                    padding: 2px 4px; 
                    background-color: white; 
                    border-radius: 2px;
                    box-sizing: border-box;">
                    ID: {row['id']}<br>{row['acreage']} ha
                </div>
                """
            )
        ).add_to(m)

# ============================
# Map legend
# ============================
legend_html = """
<div style="position: fixed; 
     top: 100px; left: 20px; width: 180px; height: 100px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px; line-height:1.3;">

<b>Legend</b><br>
🟩 Suggested Locations<br>
🟥 Existing Locations<br>
🔵 Polygon Centroids
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

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
# Download CSVs
# ============================
csv_data = gdf[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].copy()
st.sidebar.download_button(
    "📥 Download District Data (CSV)",
    data=csv_data.to_csv(index=False),
    file_name="banaskantha_castor_acreage.csv",
    mime="text/csv",
)

for pid in selected_ids:
    poly = loc_gdf[loc_gdf["id"] == pid]
    villages_inside = gpd.sjoin(gdf, poly, predicate="intersects")
    if not villages_inside.empty:
        export_df = villages_inside[["VILLAGE", "TEHSIL", "castor_ha"]].copy()
        st.sidebar.download_button(
            f"📥 Download Villages (Polygon {pid})",
            data=export_df.to_csv(index=False),
            file_name=f"polygon_{pid}_villages.csv",
            mime="text/csv",
        )
# import os
# import glob
# import streamlit as st
# import geopandas as gpd
# import folium
# from folium.features import GeoJsonTooltip
# from streamlit_folium import st_folium
# import branca.colormap as cm

# st.set_page_config(layout="wide")

# # ----------------------------
# # Helpers for paths & caching
# # ----------------------------
# def shapefile_mtime_key(shp_path: str) -> float:
#     stem = os.path.splitext(shp_path)[0]
#     sidecars = glob.glob(stem + ".*")
#     if not sidecars:
#         return 0.0
#     return max(os.path.getmtime(f) for f in sidecars)


# # ----------------------------
# # Load shapefiles
# # ----------------------------
# @st.cache_data
# def load_villages():
#     gdf = gpd.read_file(r"shp/castor_village_level_acreage_ha_new_int.shp")
#     gdf = gdf.to_crs(epsg=4326)
#     return gdf

# @st.cache_data
# def load_location_polygons():
#     gdf_loc = gpd.read_file("shp/polygons.shp")
#     gdf_loc = gdf_loc.to_crs(epsg=4326)
#     return gdf_loc


# # ============================
# # App
# # ============================
# st.title("🌱 BANAS KANTHA District - Castor Crop Acreage Dashboard")

# gdf = load_villages()
# loc_gdf = load_location_polygons()

# # ============================
# # Sidebar filters
# # ============================
# st.sidebar.title("Filters")

# # Tehsil filter
# tehsils = ["All"] + sorted(gdf["TEHSIL"].dropna().unique().tolist())
# selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils, index=0)

# # Village filter
# if selected_tehsil != "All":
#     villages = gdf.loc[gdf["TEHSIL"] == selected_tehsil, "VILLAGE"].dropna().unique().tolist()
# else:
#     villages = gdf["VILLAGE"].dropna().unique().tolist()
# villages = ["All"] + sorted(villages)
# selected_village = st.sidebar.selectbox("Select Village", villages, index=0)

# # Polygon filter
# all_ids = sorted([int(i) for i in loc_gdf["id"].unique().tolist()])
# selected_raw = st.sidebar.multiselect("Select Suggested Location IDs", ["All"] + all_ids, default="All")

# if "All" in selected_raw:
#     selected_ids = all_ids
# else:
#     selected_ids = [int(i) for i in selected_raw]

# filtered_polygons = loc_gdf[loc_gdf["id"].isin(selected_ids)]

# # ============================
# # Polygon Layer Toggles
# # ============================
# st.sidebar.subheader("Polygon Layer Controls")
# show_existing = st.sidebar.checkbox("Show Existing Locations (Red)", value=True)
# show_suggested = st.sidebar.checkbox("Show Suggested Locations (maroon)", value=True)

# # ============================
# # Data filtering
# # ============================
# filtered_gdf = gdf.copy()
# if selected_tehsil != "All":
#     filtered_gdf = filtered_gdf[filtered_gdf["TEHSIL"] == selected_tehsil]

# # Villages touching polygons
# if not filtered_polygons.empty and "All" not in selected_raw:
#     filtered_gdf = gpd.sjoin(filtered_gdf, filtered_polygons, predicate="intersects")
#     filtered_gdf = filtered_gdf.drop_duplicates(subset="VILLAGE")
#     filtered_gdf = filtered_gdf.drop(columns=["index_right"], errors="ignore")

# # ============================
# # Map setup
# # ============================
# if filtered_gdf.empty:
#     map_center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
# else:
#     map_center = [filtered_gdf.geometry.centroid.y.mean(), filtered_gdf.geometry.centroid.x.mean()]

# m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

# # Color scale for castor_ha
# ha_series = filtered_gdf["castor_ha"].dropna()
# min_val, max_val = (0, 1) if ha_series.empty else (float(ha_series.min()), float(ha_series.max()))
# colormap = cm.LinearColormap(colors=["yellow", "darkgreen"], vmin=min_val, vmax=max_val)
# colormap.caption = f"Castor Area (ha) | Min: {min_val:.2f} | Max: {max_val:.2f}"
# colormap.add_to(m)

# # Village style
# def style_function(feature):
#     village_name = feature["properties"].get("VILLAGE")
#     ha_value = feature["properties"].get("castor_ha")
#     if selected_village != "All" and village_name == selected_village:
#         return {"fillColor": "blue", "color": "black", "weight": 3, "fillOpacity": 0.8}
#     else:
#         return {
#             "fillColor": colormap(ha_value) if ha_value is not None else "grey",
#             "color": "black",
#             "weight": 1,
#             "fillOpacity": 0.6,
#         }

# if not filtered_gdf.empty:
#     folium.GeoJson(
#         filtered_gdf,
#         style_function=style_function,
#         tooltip=GeoJsonTooltip(
#             fields=["VILLAGE", "TEHSIL", "castor_ha"],
#             aliases=["Village:", "Tehsil:", "Castor (ha):"],
#             localize=True,
#         ),
#         name="Villages",
#     ).add_to(m)

# # ============================
# # Polygons overlay
# # ============================
# def style_location(feature, color):
#     return {"fillColor": color, "color": "black", "weight": 2, "fillOpacity": 0.5}

# existing_gdf = filtered_polygons[filtered_polygons["id"] > 10]
# suggested_gdf = filtered_polygons[filtered_polygons["id"] <= 10]

# # Existing polygons
# if show_existing and not existing_gdf.empty:
#     folium.GeoJson(
#         existing_gdf,
#         style_function=lambda x: style_location(x, "blue"),
#         tooltip=GeoJsonTooltip(fields=["id", "acreage"], aliases=["Location ID:", "Acreage (ha):"]),
#         name="Existing Locations",
#     ).add_to(m)

# # Suggested polygons
# if show_suggested and not suggested_gdf.empty:
#     folium.GeoJson(
#         suggested_gdf,
#         style_function=lambda x: style_location(x, "green"),
#         tooltip=GeoJsonTooltip(fields=["id", "acreage"], aliases=["Location ID:", "Acreage (ha):"]),
#         name="Suggested Locations",
#     ).add_to(m)

#     # # Add centroid points matching polygon color
#     # for _, row in filtered_polygons.iterrows():
#     #     centroid = row.geometry.centroid
#     #     color = "green" if row["id"] <= 10 else "blue"
#     #     if (color == "green" and show_suggested) or (color == "blue" and show_existing):
#     #         folium.CircleMarker(
#     #             location=[centroid.y, centroid.x],
#     #             radius=4,
#     #             color=color,
#     #             fill=True,
#     #             fill_color=color,
#     #             fill_opacity=0.6,
#     #             popup=f"ID: {row['id']}, Acreage: {row['acreage']} ha"
#     #         ).add_to(m)

# # for _, row in filtered_polygons.iterrows():
# #     centroid = row.geometry.centroid
# #     color = "green" if row["id"] <= 10 else "blue"
    
# #     if (color == "green" and show_suggested) or (color == "blue" and show_existing):
# #         # Small circle marker
# #         folium.CircleMarker(
# #             location=[centroid.y, centroid.x],
# #             radius=2,  # smaller size
# #             color=color,
# #             fill=True,
# #             fill_color=color,
# #             fill_opacity=0.4,
# #             popup=f"ID: {row['id']}, Acreage: {row['acreage']} ha"
# #         ).add_to(m)
        
# #         # Label on top
# #         folium.Marker(
# #             location=[centroid.y, centroid.x],
# #             icon=folium.DivIcon(
# #                 html=f"""
# #                 <div style="
# #                     display: inline-block;
# #                     font-size: 10px; 
# #                     color: black; 
# #                     font-weight: bold; 
# #                     text-align: center; 
# #                     line-height: 1.2; 
# #                     padding: 2px 4px; 
# #                     background-color: white; 
# #                     border-radius: 2px;
# #                     box-sizing: border-box;">
# #                     ID: {row['id']}<br>{row['acreage']} ha
# #                 </div>
# #                 """
# #             )
# #         ).add_to(m)
# for _, row in filtered_polygons.iterrows():
#     centroid = row.geometry.centroid
#     color = "green" if row["id"] <= 10 else "blue"
    
#     if (color == "green" and show_suggested) or (color == "blue" and show_existing):
#         folium.CircleMarker(
#             location=[centroid.y, centroid.x],
#             radius=5,
#             color=color,
#             fill=True,
#             fill_color=color,
#             fill_opacity=0.6,
#             popup=f"ID: {row['id']}, Acreage: {row['acreage']} ha"
#         ).add_to(m)




# # ============================
# # Map legend on top-left (adjusted to cover polygon centroids if needed)
# # ============================
# legend_html = """
# <div style="position: fixed; 
#      top: 100px; left: 20px; width: 180px; height: 100px; 
#      border:2px solid grey; z-index:9999; font-size:14px;
#      background-color:white; padding: 10px; line-height:1.3;">

# <b>Legend</b><br>
# 🟩 Suggested Locations<br>
# 🟥 Existing Locations<br>
# 🔵 Polygon Centroids
# </div>


# """
# m.get_root().html.add_child(folium.Element(legend_html))

# # ============================
# # Map -> Streamlit
# # ============================
# st_data = st_folium(m, width=1000, height=650)

# # ============================
# # Village info panel
# # ============================
# village_info = None
# if st_data and "last_active_drawing" in st_data and st_data["last_active_drawing"]:
#     props = st_data["last_active_drawing"]["properties"]
#     village_info = {
#         "Village": props.get("VILLAGE"),
#         "Tehsil": props.get("TEHSIL"),
#         "Castor Area (ha)": props.get("castor_ha"),
#     }
# elif selected_village != "All":
#     sel_row = filtered_gdf[filtered_gdf["VILLAGE"] == selected_village]
#     if not sel_row.empty:
#         village_info = {
#             "Village": sel_row["VILLAGE"].values[0],
#             "Tehsil": sel_row["TEHSIL"].values[0],
#             "Castor Area (ha)": sel_row["castor_ha"].values[0],
#         }

# if village_info:
#     st.sidebar.subheader("Village Information")
#     for k, v in village_info.items():
#         st.sidebar.write(f"**{k}:** {v}")

# # ============================
# # Download CSVs
# # ============================
# csv_data = gdf[["DISTRICT", "TEHSIL", "VILLAGE", "castor_ha"]].copy()
# st.sidebar.download_button(
#     "📥 Download District Data (CSV)",
#     data=csv_data.to_csv(index=False),
#     file_name="banaskantha_castor_acreage.csv",
#     mime="text/csv",
# )

# for pid in selected_ids:
#     poly = loc_gdf[loc_gdf["id"] == pid]
#     villages_inside = gpd.sjoin(gdf, poly, predicate="intersects")
#     if not villages_inside.empty:
#         export_df = villages_inside[["VILLAGE", "TEHSIL", "castor_ha"]].copy()
#         st.sidebar.download_button(
#             f"📥 Download Villages (Polygon {pid})",
#             data=export_df.to_csv(index=False),
#             file_name=f"polygon_{pid}_villages.csv",
#             mime="text/csv",
#         )
