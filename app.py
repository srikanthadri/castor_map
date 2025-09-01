import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide")
st.title("Village-level Castor Area Map")

# --- Load shapefile ---
shapefile_path = "village_data.shp"  # change path if needed
gdf = gpd.read_file(shapefile_path)

# --- Debug: check field names ---
props = json.loads(gdf.to_json())["features"][0]["properties"]
st.write("Available properties in GeoJSON:", props.keys())

# --- Ensure column is numeric ---
gdf["castor_ha"] = gdf["castor_ha"].astype(float)

# --- Create Folium map ---
m = folium.Map(location=[20, 78], zoom_start=6, tiles="cartodbpositron")

# Choropleth (use lowercase 'village' if fields are converted)
folium.Choropleth(
    geo_data=gdf.to_json(),
    name="Castor Area",
    data=gdf,
    columns=["VILLAGE", "castor_ha"],  # keep uppercase here (matches shapefile column name)
    key_on="feature.properties.village",  # 🔑 lowercase fix
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Castor Area (ha)"
).add_to(m)

# Add tooltips
folium.GeoJson(
    gdf,
    style_function=lambda x: {"fillColor": "transparent", "color": "black", "weight": 0.5},
    tooltip=folium.GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "castor_ha"],
        aliases=["Village:", "Tehsil:", "District:", "Castor Area (ha):"],
        localize=True
    )
).add_to(m)

# Show map in Streamlit
st_folium(m, width=1000, height=700)
