import pandas as pd
import streamlit

from scripts.calculate_vital_distances import calculate_vital_distances
from scripts.compare_vital_distances import compare_vital_distances


def show_compare_algos():
    streamlit.text('''
    So obviously the grid approach has its limitations.
    We should generate candidate locations close to existing hotspots of cardiac arrests.
    This will allow us to evaluate more relevant locations.
    In this part we will compare both approaches to see which one yields better results for the same number of candidate locations: 10k.
    ''')

        # Calculate vital distances for the grid-based approach
    calculate_vital_distances('filtered_potential_aed_locations.csv')
    grid_vital_distances = pd.read_csv('transformed_data/distance/filtered_potential_aed_locations.csv')

    # Calculate vital distances for the center-of-gravity-based approach
    calculate_vital_distances('centers_of_gravity_potential_aed_locations.csv')
    cog_vital_distances = pd.read_csv('transformed_data/distance/centers_of_gravity_potential_aed_locations.csv')

    # Compare the results
    grid_max_vital_distance = grid_vital_distances['distance'].max()
    cog_max_vital_distance = cog_vital_distances['distance'].max()

    compare_vital_distances(
       'centers_of_gravity_potential_aed_locations.csv',
       'new_aeds_grid.csv'
    )

    if grid_max_vital_distance > cog_max_vital_distance:
        print("The grid-based approach yields the highest vital distance.")
    elif cog_max_vital_distance > grid_max_vital_distance:
        print("The center-of-gravity-based approach yields the highest vital distance.")
    else:
        print("Both approaches yield the same maximum vital distance.")


