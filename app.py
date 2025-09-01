import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide")
st.title("Village-level Castor Area Map")

# --- Load shapefile ---
shapefile_path = "castor_village_level_acreage_ha.shp"  # adjust path if needed
gdf = gpd.read_file(shapefile_path)

# --- Debug: show property names from GeoJSON ---
geojson_data = json.loads(gdf.to_json())
props = geojson_data["features"][0]["properties"]
st.write("Available properties in GeoJSON:", list(props.keys()))

# --- Ensure castor_ha is numeric ---
gdf["castor_ha"] = gdf["castor_ha"].astype(float)

# --- Create Folium map ---
m = folium.Map(location=[20, 78], zoom_start=6, tiles="cartodbpositron")

# ✅ Choropleth
folium.Choropleth(
    geo_data=gdf.to_json(),                # always use to_json()
    name="Castor Area",
    data=gdf,
    columns=["VILLAGE", "castor_ha"],      # must match gdf column names
    key_on="feature.properties.VILLAGE",   # must match GeoJSON property name
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Castor Area (ha)"
).add_to(m)

# ✅ Tooltips
folium.GeoJson(
    gdf.to_json(),
    style_function=lambda x: {"fillColor": "transparent", "color": "black", "weight": 0.5},
    tooltip=folium.GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
        aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
        localize=True
    )
).add_to(m)

# --- Show map in Streamlit ---
st_folium(m, width=1000, height=700)
