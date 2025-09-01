import streamlit as st
import folium
import geopandas as gpd
from streamlit_folium import st_folium

# Load shapefile
shapefile_path = "your_shapefile.shp"   # change to your shapefile path
gdf = ggpd.read_file("castor_village_level_acreage_ha.shp")pd.read_file(shapefile_path)

# Convert to GeoJSON string
gdf_json = gdf.to_json()

# Create Folium Map
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

# Add Choropleth
folium.Choropleth(
    geo_data=gdf_json,
    name="Castor Hectares",
    data=gdf,
    columns=["VILLAGE", "castor_ha"],   # joining field and values
    key_on="feature.properties.VILLAGE",  # join key in GeoJSON
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Castor Area (ha)"
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

