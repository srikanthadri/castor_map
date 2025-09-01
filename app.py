import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors

# Load shapefile
shapefile_path = r"castor_village_level_acreage_ha.shp"
gdf = gpd.read_file(shapefile_path)

# Drop rows with missing TEHSIL or VILLAGE to avoid NoneType errors
gdf = gdf.dropna(subset=["TEHSIL", "VILLAGE"])

st.title("Tehsil & Village Dashboard")

# Sidebar filters
tehsil_options = ["All"] + sorted(gdf["TEHSIL"].unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsil_options)

if selected_tehsil == "All":
    filtered_gdf = gdf
else:
    filtered_gdf = gdf[gdf["TEHSIL"] == selected_tehsil]

village_options = ["All"] + sorted(filtered_gdf["VILLAGE"].unique().tolist())
selected_village = st.sidebar.selectbox("Select Village", village_options)

# Base map (zoom on filtered area)
if not filtered_gdf.empty:
    center = filtered_gdf.geometry.centroid.unary_union.centroid.coords[0][::-1]
    m = folium.Map(location=center, zoom_start=10)
else:
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

# Color map for castor_ha
min_val, max_val = gdf["castor_ha"].min(), gdf["castor_ha"].max()
colormap = cm.ScalarMappable(norm=colors.Normalize(vmin=min_val, vmax=max_val), cmap="YlOrRd")

# Add polygons
for _, row in filtered_gdf.iterrows():
    color = colors.to_hex(colormap.to_rgba(row["castor_ha"]))
    folium.GeoJson(
        row["geometry"],
        style_function=lambda feature, color=color: {
            "fillColor": color,
            "color": "black" if row["VILLAGE"] == selected_village else "gray",
            "weight": 3 if row["VILLAGE"] == selected_village else 1,
            "fillOpacity": 0.7,
        },
        tooltip=folium.Tooltip(
            f"Village: {row['VILLAGE']}<br>Tehsil: {row['TEHSIL']}<br>Castor (ha): {row['castor_ha']}"
        ),
    ).add_to(m)

# Add legend colorbar
from branca.colormap import LinearColormap
linear = LinearColormap(
    colors=["#ffffb2","#fecc5c","#fd8d3c","#f03b20","#bd0026"],
    vmin=min_val, vmax=max_val,
    caption="Castor Area (ha)"
)
linear.add_to(m)

# Show map
st_folium(m, width=800, height=600)



