import geopandas as gpd
import folium

# Load shapefile
gdf = gpd.read_file("castor_village_level_acreage_ha.shp")

# Ensure castor_ha is numeric
gdf["castor_ha"] = gdf["castor_ha"].astype(float)

# Get centroid of the state to set map center
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]

# Create folium map
m = folium.Map(location=center, zoom_start=8, tiles="CartoDB positron")

# Choropleth map based on castor_ha
choropleth = folium.Choropleth(
    geo_data=gdf,
    name="Castor Acreage",
    data=gdf,
    columns=["VILLAGE", "castor_ha"],
    key_on="feature.properties.VILLAGE",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Castor Area (ha)",
).add_to(m)

# Add tooltips (on hover show details)
folium.GeoJsonTooltip(
    fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
    aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
    sticky=True
).add_to(choropleth.geojson)

# Highlight selected village on click
highlight = folium.GeoJson(
    gdf,
    style_function=lambda x: {"fillColor": "transparent", "color": "blue", "weight": 2},
    highlight_function=lambda x: {"weight": 4, "color": "red"},
    tooltip=folium.GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "castor_ha"],
        aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
    ),
).add_to(m)

# Add Layer control
folium.LayerControl().add_to(m)

# Save map
m.save("castor_village_map.html")
