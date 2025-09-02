import streamlit as st
import geopandas as gpd
import folium
from folium import GeoJson
from streamlit_folium import st_folium

# ----------------------------
# Load shapefile for suggested points
# ----------------------------
@st.cache_data
def load_points():
    points = gpd.read_file("shp//suggested_points.shp")  # ensure updated file is here
    points = points.to_crs(epsg=4326)
    return points

# ----------------------------
# Create buffer polygons around points
# ----------------------------
@st.cache_data
def create_buffers(points_gdf, distance_km=25):
    return points_gdf.to_crs(epsg=3857).buffer(distance_km * 1000).to_crs(epsg=4326)

# ----------------------------
# Main function
# ----------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("🌍 Suggested Villages Dashboard")

    # Load data
    try:
        points_gdf = load_points()
    except Exception as e:
        st.error(f"Error loading shapefile: {e}")
        return

    # If no data
    if points_gdf.empty:
        st.warning("No points found in shapefile.")
        return

    # Create buffer polygons
    buffer_gdf = create_buffers(points_gdf)

    # Sidebar controls
    st.sidebar.header("⚙️ Controls")

    # Use NAME column if available
    if "NAME" in points_gdf.columns:
        village_options = points_gdf["NAME"].tolist()
    else:
        village_options = [f"Point {i}" for i in range(len(points_gdf))]

    selected_village = st.sidebar.selectbox("Select a Village", village_options)

    show_points = st.sidebar.checkbox("Show Suggested Points", value=True)
    show_buffers = st.sidebar.checkbox("Show Buffer (25 km)", value=True)

    # Map center
    center = [points_gdf.geometry.y.mean(), points_gdf.geometry.x.mean()]
    m = folium.Map(location=center, zoom_start=7, tiles="cartodbpositron")

    # Add suggested points
    if show_points:
        for _, row in points_gdf.iterrows():
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=row["NAME"] if "NAME" in points_gdf.columns else "Point",
                icon=folium.Icon(color="red", icon="map-marker")
            ).add_to(m)

    # Add buffer polygons
    if show_buffers:
        GeoJson(
            buffer_gdf,
            name="Buffers",
            style_function=lambda x: {
                "color": "blue",
                "fillColor": "lightblue",
                "fillOpacity": 0.3,
                "weight": 2,
            }
        ).add_to(m)

    # Highlight selected village
    if selected_village:
        if "NAME" in points_gdf.columns:
            sel_point = points_gdf[points_gdf["NAME"] == selected_village]
            sel_buffer = buffer_gdf.loc[sel_point.index]
        else:
            idx = village_options.index(selected_village)
            sel_point = points_gdf.iloc[[idx]]
            sel_buffer = buffer_gdf.iloc[[idx]]

        # Highlight selected point
        GeoJson(
            sel_point,
            name="Selected Village",
            style_function=lambda x: {"color": "red"}
        ).add_to(m)

        # Highlight selected buffer
        GeoJson(
            sel_buffer,
            name="Selected Buffer",
            style_function=lambda x: {
                "color": "red",
                "fillColor": "pink",
                "fillOpacity": 0.4,
                "weight": 2,
            }
        ).add_to(m)

        # Zoom to selected buffer
        m.fit_bounds(sel_buffer.total_bounds.reshape(2, 2).tolist())

    # Layer control
    folium.LayerControl().add_to(m)

    # Show in Streamlit
    st_folium(m, width=1000, height=600)

if __name__ == "__main__":
    main()
