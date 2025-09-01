import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium 
from branca.colormap import linear

# Load shapefile
shapefile_path = "castor_village_level_acreage_ha.shp"  # change path
gdf = gpd.read_file(shapefile_path)

# Ensure column names are clean
gdf.columns = gdf.columns.str.strip()

# Sidebar filters
tehsils = ["All"] + sorted(gdf["TEHSIL"].unique().tolist())
selected_tehsil = st.sidebar.selectbox("Select Tehsil", tehsils)

if selected_tehsil == "All":
    filtered_tehsil = gdf
else:
    filtered_tehsil = gdf[gdf["TEHSIL"] == selected_tehsil]

villages = ["All"] + sorted(filtered_tehsil["VILLAGE"].unique().tolist())
selected_village = st.sidebar.selectbox("Select Village", villages)

# Main map
m = folium.Map(location=[filtered_tehsil.geometry.centroid.y.mean(),
                         filtered_tehsil.geometry.centroid.x.mean()],
               zoom_start=8)

# Create color map based on 'castor_ha'
colormap = linear.YlGnBu_09.scale(gdf["castor_ha"].min(), gdf["castor_ha"].max())
colormap.caption = "Castor area (ha)"
colormap.add_to(m)

# Add polygons
for _, row in filtered_tehsil.iterrows():
    color = colormap(row["castor_ha"])
    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, color=color: {
            "fillColor": color,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        tooltip=f"Village: {row['VILLAGE']}<br>Tehsil: {row['TEHSIL']}<br>HA: {row['castor_ha']}"
    ).add_to(m)

# Highlight selected village
if selected_village != "All":
    village_row = filtered_tehsil[filtered_tehsil["VILLAGE"] == selected_village]
    if not village_row.empty:
        folium.GeoJson(
            village_row.geometry,
            style_function=lambda x: {
                "fillColor": "red",
                "color": "yellow",
                "weight": 3,
                "fillOpacity": 0.9,
            },
            tooltip=f"Village: {village_row['VILLAGE'].values[0]}<br>Tehsil: {village_row['TEHSIL'].values[0]}<br>HA: {village_row['castor_ha'].values[0]}"
        ).add_to(m)
        # Zoom to selected village
        m.fit_bounds(village_row.geometry.total_bounds.reshape(2,2).tolist())

# Display map in Streamlit
st_folium(m, width=800, height=600)

