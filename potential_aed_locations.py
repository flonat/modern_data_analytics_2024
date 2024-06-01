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

    st.write("This is very inefficient. It covers parts that are not even in Belgium! Let's only consider locations that are at least 1km from existing cardiac arrests.")
    st.write("The will use a brute force approach. We take a dot on the grid and then go through the list of existing cardiac arrest locations. We run through the list. If it's in the radius of an existing cardiac arrest we keep it. If not we discart the candidate location")

    if st.button('Run selection of grid dots'):
        df_interventions = pd.read_csv('./transformed_data/location/arrests.csv')

        # Convert the intervention locations to a GeoDataFrame
        gdf_interventions = gpd.GeoDataFrame(
            df_interventions, 
            geometry=gpd.points_from_xy(df_interventions.lon, df_interventions.lat), 
            crs='epsg:4326'
        )

        # Project the intervention locations to the Cartesian system
        gdf_interventions['x'], gdf_interventions['y'] = transform(wgs84, utm32n, gdf_interventions['lon'].values, gdf_interventions['lat'].values)

        #  Initialize an empty DataFrame to store the potential AED locations
        df_potential_locations = pd.DataFrame(columns=['lat', 'lon'])

        progress_text = st.empty()
        progress_bar = st.progress(0)
        # Iterate over the potential AED locations
        for index, row in map_df.iterrows():
            progress_text.text('Total done: ' + str(index + 1) + ' out of ' + str(len(map_df)))
            progress_bar.progress(index / len(map_df))
            print('Vetting location ' + str(index))
            potential_location = (row['lat'], row['lon'])
            # Project the potential location to the Cartesian system
            x, y = transform(wgs84, utm32n, potential_location[1], potential_location[0])
            # Iterate over the intervention locations
            for _, intervention in gdf_interventions.iterrows():
                intervention_location = (intervention['x'], intervention['y'])
                # Calculate the distance between the potential location and the intervention location
                distance = np.sqrt((x - intervention_location[0])**2 + (y - intervention_location[1])**2)
                # If the distance is less than 1km (1000m in Cartesian system), add the potential location to the DataFrame
                if distance < 1000:
                    print('we found a valid location')
                    df_potential_locations.loc[len(df_potential_locations)] = [row['lat'], row['lon']]
                    # Break the loop as we found a valid location
                    break

        # Save the DataFrame to a CSV file for future use
        df_potential_locations.to_csv('transformed_data/filtered_potential_aed_locations.csv', index=False)

        # Display the DataFrame in the Streamlit app
        st.write("Here are the filtered potential AED locations:")
        st.write(df_potential_locations)

    # Check if the filtered potential AED locations file exists
    if os.path.exists('transformed_data/filtered_potential_aed_locations.csv'):
        # Load the DataFrame from the CSV file
        df_filtered_potential_locations = pd.read_csv('transformed_data/filtered_potential_aed_locations.csv')

        # Display the filtered potential AED locations on a map in the Streamlit app
        st.write("Displayed on a map")
        st.map(df_filtered_potential_locations)
    else:
        st.write("The filtered potential AED locations file does not exist. Run the filtering first")
    
    st.write("Ok this is already looking better. We are focussing on areas that have cardiac arrests. We will analyse less useless potential AED locations in the middle of nowhere")
    st.write("We can still do better though. Instead of creating a grid and then filtering the interesting candidates we can first determine the centers of gravity of the cardiac arrest occuring. We could then generate the candidate AED locations around those centers.")

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