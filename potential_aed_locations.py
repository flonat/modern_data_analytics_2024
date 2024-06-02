import streamlit as st

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Proj, transform
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
from sklearn.cluster import KMeans

# Define a projection from longitude,latitude to Cartesian system
wgs84 = Proj('epsg:4326')  # WGS84 (longitude, latitude)
utm32n = Proj('epsg:32632')  # UTM zone 32N (Cartesian system)


def show_potential_locations():
    # This function is used to show potential locations for AEDs on a map

    st.title('Creating candidate locations for new AEDs')

    st.write("""
This section is designed to help identify potential locations for AEDs using two distinct approaches: 
a simple grid-based system and a more advanced K-means clustering method.
The grid-based system generates a grid of latitude and longitude points within defined geographical boundaries, providing a straightforward, evenly distributed set of potential AED locations.
The K-means clustering method, on the other hand, identifies centers of gravity of cardiac arrest occurrences and generates potential AED locations around these centers. This approach allows for more targeted placement of AEDs in areas with higher incidences of cardiac arrests.
You can customize the number of centers of gravity, the number of candidate locations, and the radius around the center of gravity. The potential AED locations are displayed on a map for easy visualization. This tool aims to assist in strategic planning of AED placements, potentially improving response times in emergency situations and saving lives.
             """)


    # Define Belgium's boundary using a simplified polygon or use an actual shapefile
    # This is not implemented yet, but you can use the commented line below as a starting point
    # gdf_belgium = gpd.read_file('./be_1km.shp') 

    # Define the latitude and longitude boundaries for the area of interest
    lat_start, lat_end = 49.5, 51.5
    lon_start, lon_end = 2.5, 6.4

    # Define the number of points in the latitude and longitude directions
    # Increase these numbers to make the mesh finer
    lat_points, lon_points = 100, 100 

    # Generate a grid of latitude and longitude points within the defined boundaries
    latitudes = np.linspace(lat_start, lat_end, lat_points)
    longitudes = np.linspace(lon_start, lon_end, lon_points)
    lat_grid, lon_grid = np.meshgrid(latitudes, longitudes)
    coordinates = np.vstack([lat_grid.ravel(), lon_grid.ravel()]).T

    # Convert the grid points to a GeoDataFrame for further processing
    points = [Point(lon, lat) for lon, lat in coordinates]
    gdf_points = gpd.GeoDataFrame(geometry=points, crs='epsg:4326')

    # Extract the latitude and longitude from the GeoDataFrame and convert to a list
    map_data = gdf_points.geometry.apply(lambda p: {
        'lon': p.x,
        'lat': p.y
    }).tolist()

    # Convert the list to a DataFrame for easier manipulation and saving
    map_df = pd.DataFrame(map_data)
    map_df.columns = ['lat', 'lon']

    # Save the DataFrame to a CSV file for future use
    map_df.to_csv('transformed_data/potential_aed_locations.csv', index=False)

    # Display the DataFrame in the Streamlit app
    st.write("Here are the potential AED locations:")
    st.write(map_df)

    # Display the potential AED locations on a map in the Streamlit app
    st.write("Grid displayed on a map")
    st.map(map_df)

    
    st.write("We can do better though. Instead of creating a grid we can first determine the centers of gravity of the cardiac arrest occuring. We could then generate the candidate AED locations around those centers.")

    N = st.number_input('Number of centers of gravity', min_value=1, max_value=100, value=10)

    # Define the number of points to generate within the circle
    num_points_per_center = st.number_input('Number of candidate locations', min_value=1, max_value=10000, value=100)

    # Define the radius around the center of gravity
    # radius = 2  # in km
    radius = st.number_input('Radius around the center of gravity (in km)', min_value=1, max_value=100, value=2)

    if st.button('Run clustering'):
        df_interventions = pd.read_csv('./transformed_data/location/arrests.csv')
        # Define the number of centers of gravity
        # Get the centers of gravity
        centers = get_centers_of_gravity(df_interventions, N)


        # Generate candidate locations
        df_potential_locations = generate_candidate_locations(centers, radius, num_points_per_center)

        # Save the DataFrame to a CSV file for future use
        df_potential_locations.to_csv('transformed_data/centers_of_gravity_potential_aed_locations.csv', index=False)

        # Display the DataFrame in the Streamlit app
        st.write("Here are the potential AED locations based on centers of gravity:")
        st.write(df_potential_locations)

        # Display the potential AED locations on a map in the Streamlit app
        st.map(df_potential_locations)

def get_centers_of_gravity(df, N):
    # Run K-means clustering
    kmeans = KMeans(n_clusters=N, random_state=0).fit(df[['lat', 'lon']])

    # Get the centers of gravity
    centers = kmeans.cluster_centers_

    return centers

def generate_candidate_locations(centers, radius, num_points):
    # Initialize an empty DataFrame to store the potential AED locations
    df_potential_locations = pd.DataFrame(columns=['lat', 'lon'])

    # Iterate over the centers of gravity
    for center in centers:
        # Generate points within the circle
        for _ in range(num_points):
            # Generate a random radius and angle
            r = radius * np.sqrt(np.random.rand())
            angle = 2 * np.pi * np.random.rand()

            # Calculate the new latitude and longitude
            new_lat = center[0] + r * np.cos(angle) / 111.32  # divide by 111.32 to convert km to degrees
            new_lon = center[1] + r * np.sin(angle) / (111.32 * np.cos(center[0]))  # divide by 111.32*cos(lat) to convert km to degrees

            # Add the new location to the DataFrame
            df_potential_locations.loc[len(df_potential_locations)] = [new_lat, new_lon]

    return df_potential_locations

def format_coordinates(longitude):
    # This function is used to format the longitude to 6 decimal places
    formatted_longitude = "{:.6f}".format(longitude)
    return formatted_longitude