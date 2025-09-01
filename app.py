import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip


# Load shapefile
gdf = gpd.read_file("castor_village_level_acreage_ha.shp")

# Ensure castor_ha is numeric
gdf["castor_ha"] = gdf["castor_ha"].astype(float)

# Get centroid of the layer for map center
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]

# Create folium map
m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

# Choropleth map based on castor_ha
choropleth = folium.Choropleth(
    geo_data=gdf,
    name="Castor Acreage",
    data=gdf,
    columns=["VILLAGE", "castor_ha"],
    key_on="feature.properties.VILLAGE",
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Castor Area (ha)",
    highlight=True
).add_to(m)

# Add tooltips (hover info)
GeoJsonTooltip(
    fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
    aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
    sticky=True
).add_to(choropleth.geojson)

# Highlight boundaries on hover/click
folium.GeoJson(
    gdf,
    style_function=lambda x: {"fillColor": "transparent", "color": "black", "weight": 0.5},
    highlight_function=lambda x: {"weight": 3, "color": "yellow"},
    tooltip=GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
        aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
    ),
).add_to(m)

# Add Layer control
folium.LayerControl().add_to(m)

# Save map
m.save("castor_village_map.html")
