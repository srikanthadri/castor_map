import streamlit as st
import folium
import geopandas as gpd
from streamlit_folium import st_folium

# Load shapefile
import geopandas as gpd

# If your shapefile is named like this:
shapefile_path = "castor_village_level_acreage_ha.shp"

# Correctly load the shapefile
gdf = gpd.read_file(shapefile_path)


# Convert to GeoJSON string
gdf_json = gdf.to_json()

# Create Folium Map
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

# Add Choropleth
choropleth = folium.Choropleth(
    geo_data=gdf.__geo_interface__,
    data=gdf,
    columns=["VILLAGE", "castor_ha"],
    key_on="feature.properties.VILLAGE",  # ✅ fixed
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Castor Acreage (ha)"
).add_to(m)


# Add tooltips
folium.GeoJson(
    gdf_json,
    name="Labels",
    tooltip=folium.GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
        aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
        localize=True
    )
).add_to(m)

# Render map in Streamlit
st.title("Castor Area by Village")
st_folium(m, width=900, height=600)

