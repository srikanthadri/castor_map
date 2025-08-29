{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "33656ef1-0d00-4c04-8b99-bd5cb5e645b5",
   "metadata": {},
   "outputs": [],
   "source": [
    "import streamlit as st\n",
    "import geopandas as gpd\n",
    "import folium\n",
    "from streamlit_folium import st_folium\n",
    "\n",
    "# Load shapefile\n",
    "@st.cache_data\n",
    "def load_data():\n",
    "    gdf = gpd.read_file(\"D:\\\\castor_map\\\\villages.shp\")  # replace with your shapefile\n",
    "    return gdf\n",
    "\n",
    "gdf = load_data()\n",
    "\n",
    "st.title(\"Village Area Dashboard\")\n",
    "\n",
    "# Dropdowns\n",
    "districts = sorted(gdf[\"District\"].unique())\n",
    "district = st.selectbox(\"Select District\", districts)\n",
    "\n",
    "blocks = sorted(gdf[gdf[\"District\"] == district][\"Block\"].unique())\n",
    "block = st.selectbox(\"Select Block\", blocks)\n",
    "\n",
    "villages = gdf[(gdf[\"District\"] == district) & (gdf[\"Block\"] == block)]\n",
    "village = st.selectbox(\"Select Village\", sorted(villages[\"Village\"].unique()))\n",
    "\n",
    "# Show area\n",
    "selected = villages[villages[\"Village\"] == village]\n",
    "area = selected.iloc[0][\"Area\"]\n",
    "st.metric(\"Village Area (hectares)\", f\"{area:.2f}\")\n",
    "\n",
    "# Map\n",
    "m = folium.Map(location=[selected.geometry.centroid.y.values[0],\n",
    "                         selected.geometry.centroid.x.values[0]], zoom_start=12)\n",
    "folium.GeoJson(selected).add_to(m)\n",
    "st_folium(m, width=700, height=500)\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
