import geopandas as gpd
import folium

# --- Load shapefile ---
gdf = gpd.read_file("castor_village_level_acreage_ha.shp")

# --- Clean column names (remove spaces, force uppercase) ---
gdf.columns = gdf.columns.str.strip().str.upper()

# --- Ensure castor_ha is numeric ---
gdf["CASTOR_HA"] = gdf["CASTOR_HA"].astype(float)

# --- Reproject before centroid warning ---
gdf = gdf.to_crs(epsg=4326)  # WGS84 (lat/lon)
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]

# --- Create folium map ---
m = folium.Map(location=center, zoom_start=8, tiles="CartoDB positron")

# ✅ Choropleth
choropleth = folium.Choropleth(
    geo_data=gdf.to_json(),   # use JSON, not raw gdf
    name="Castor Acreage",
    data=gdf,
    columns=["VILLAGE", "CASTOR_HA"],   # after cleanup, uppercase
    key_on="feature.properties.VILLAGE",  # ✅ now matches cleaned column
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Castor Area (ha)",
).add_to(m)

# ✅ Tooltip
folium.GeoJson(
    gdf,
    style_function=lambda x: {"fillColor": "transparent", "color": "blue", "weight": 0.5},
    tooltip=folium.GeoJsonTooltip(
        fields=["VILLAGE", "TEHSIL", "DISTRICT", "STATE", "CASTOR_HA"],
        aliases=["Village:", "Tehsil:", "District:", "State:", "Castor Area (ha):"],
        sticky=True
    )
).add_to(m)

# Layer control
folium.LayerControl().add_to(m)

# --- Save map to HTML ---
m.save("castor_village_map.html")
print("✅ Map saved as castor_village_map.html")
