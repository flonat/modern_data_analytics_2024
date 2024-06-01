import pandas as pd
import sys
import numpy as np
from scripts.paths import LOCATION_PATH, DISTANCE_PATH, DISTANCE_PATH, COMPARE_PATH
from scripts.calculate_vital_distances import calculate_vital_distances

def nest_list(group):
    return group.tolist()

def compare_vital_distances(new_aed_csv, old_aed_csv='old_aeds.csv'):
    print(f'Comparing vital distances between {new_aed_csv} and {old_aed_csv}')
    # Get vital distances & locations
    if not (DISTANCE_PATH / new_aed_csv).exists():
        calculate_vital_distances(new_aed_csv)
    if not (DISTANCE_PATH / old_aed_csv).exists():
        calculate_vital_distances(old_aed_csv)

    new_distances = pd.read_csv(DISTANCE_PATH / new_aed_csv)
    old_distances = pd.read_csv(DISTANCE_PATH / old_aed_csv)
    new_locations = pd.read_csv(LOCATION_PATH / new_aed_csv)
    old_locations = pd.read_csv(LOCATION_PATH / old_aed_csv)
    arrest_locations = pd.read_csv(LOCATION_PATH / 'arrests.csv')

    # Get arrests with closer new AEDs
    arrest_with_closer_new_aeds = new_distances.loc[new_distances['distance'] < old_distances['distance']]
    arrest_with_closer_new_aeds = arrest_with_closer_new_aeds.reset_index()
    arrest_with_closer_new_aeds.columns = ['arrest', 'new_aed', 'new_distance']

    # Get arrest, new AED, and old AED information
    arrest_with_closer_new_aeds = pd.merge(arrest_with_closer_new_aeds, old_distances, left_on='arrest', right_index=True).rename(columns={'index': 'old_aed', 'distance': 'old_distance'})
    arrest_with_closer_new_aeds = pd.merge(arrest_with_closer_new_aeds, arrest_locations, left_on='arrest', right_index=True).rename(columns={'lat': 'arrest_lat', 'lon': 'arrest_lon'})
    arrest_with_closer_new_aeds = pd.merge(arrest_with_closer_new_aeds, new_locations, left_on='new_aed', right_index=True).rename(columns={'lat': 'new_lat', 'lon': 'new_lon'})
    arrest_with_closer_new_aeds = pd.merge(arrest_with_closer_new_aeds, old_locations, left_on='old_aed', right_index=True).rename(columns={'lat': 'old_lat', 'lon': 'old_lon'})

    # Group by new AED
    closer_new_aeds = arrest_with_closer_new_aeds.groupby('new_aed', as_index=False).agg(
        arrest_count=('arrest', 'nunique'),
        new_distance=('new_distance', nest_list),
        new_lat=('new_lat', 'max'),
        new_lon=('new_lon', 'max'),
        arrest=('arrest', nest_list),
        arrest_lat=('arrest_lat', nest_list),
        arrest_lon=('arrest_lon', nest_list),
        old_aed=('old_aed', nest_list),
        old_distance=('old_distance', nest_list),
        old_lat=('old_lat', nest_list),
        old_lon=('old_lon', nest_list)).sort_values(by='arrest_count', ascending=False)

    closer_new_aeds.rename({
        'new_aed': 'potential_aed_id',
        'new_distance': 'distance_to_potential_aed',
        'new_lat': 'potential_aed_lat',
        'new_lon': 'potential_aed_lon',
        'arrest': 'intervention_id',
        'arrest_lat': 'intervention_lat',
        'arrest_lon': 'intervention_lon',
        'old_aed': 'existing_aed_id',
        'old_distance': 'distance_to_existing_aed',
        'old_lat': 'existing_aed_lat',
        'old_lon': 'existing_aed_lon'
    }, axis=1, inplace=True)

    new_aed_filename = new_aed_csv.split('.')[0] if '.csv' in new_aed_csv else new_aed_csv
    closer_new_aeds.to_csv(COMPARE_PATH / f'{new_aed_filename}__{old_aed_csv}', index=False)
        
if __name__ == '__main__':
    if len(sys.argv) > 2:
        compare_vital_distances(sys.argv[1], sys.argv[2])
    else:
        print('No old AED file provided, using old_aeds.csv')
        compare_vital_distances(sys.argv[1], 'old_aeds.csv')