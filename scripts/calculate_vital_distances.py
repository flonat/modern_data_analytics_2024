import sys

import pandas as pd
import sys
import numpy as np
from paths import LOCATION_PATH, DISTANCE_PATH


from sklearn.metrics.pairwise import haversine_distances

def calculate_distances(arrest_locations, aed_locations):
    return haversine_distances(np.radians(arrest_locations), np.radians(aed_locations)) * 6371000/1000

def calculate_vital_distances(aed_csv='old_aeds.csv'):
    arrest_locations = pd.read_csv(LOCATION_PATH / 'arrests.csv').values
    aed_locations = pd.read_csv(LOCATION_PATH / aed_csv).values

    print(f'Calculating vital distances between {len(arrest_locations)} arrests and {len(aed_locations)} AED in {aed_csv}')
    distances = calculate_distances(arrest_locations, aed_locations)

    # Calculate vital distance for each arrest
    vital_distances = pd.DataFrame({'index': np.argmin(distances, axis=1), 'distance': np.min(distances, axis=1)})

    # Save distances
    vital_distances.to_csv(DISTANCE_PATH / aed_csv, index=False)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print('Calculating vital distances of', sys.argv[1])
        calculate_vital_distances(sys.argv[1])
    else:
        print('No AED locations file provided, using old_aeds.csv')
        calculate_vital_distances('old_aeds.csv')