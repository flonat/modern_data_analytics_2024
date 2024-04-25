import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

def show_potential_locations():
    # Define Belgium's boundary using a simplified polygon or use an actual shapefile

    # Create a GeoDataFrame for the boundary
    # DID NOT IMPLEMENT IT YET!
    # gdf_belgium = gpd.read_file('./be_1km.shp') 


    # Generate points as previously
    lat_start, lat_end = 49.5, 51.5
    lon_start, lon_end = 2.5, 6.4

    # CHANGE HERE TO MAKE THE MESH SMALLER
    lat_points, lon_points = 100, 100 
    latitudes = np.linspace(lat_start, lat_end, lat_points)
    longitudes = np.linspace(lon_start, lon_end, lon_points)
    lat_grid, lon_grid = np.meshgrid(latitudes, longitudes)
    coordinates = np.vstack([lat_grid.ravel(), lon_grid.ravel()]).T

    # Create a GeoDataFrame for the points
    points = [Point(lon, lat) for lon, lat in coordinates]
    gdf_points = gpd.GeoDataFrame(geometry=points, crs='epsg:4326')

    map_data = gdf_points.geometry.apply(lambda p: {
        'lon': p.x,
        'lat': p.y
    }).tolist()

    map_df = pd.DataFrame(map_data)
    map_df.columns = ['lat', 'lon']

    map_df.to_csv('transformed_data/potential_aed_locations.csv', index=False)
    st.write(map_df)
    st.map(map_df)

def format_coordinates(longitude):
    formatted_longitude = "{:.6f}".format(longitude)
    return formatted_longitude