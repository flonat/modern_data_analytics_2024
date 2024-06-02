import pandas as pd
import googlemaps
from scripts.paths import COMPARE_PATH


# Replace 'YOUR_API_KEY' with your actual API key
gmaps = googlemaps.Client(key='your_googlemap_api')

def get_province(row):
    # Perform reverse geocoding
    result = gmaps.reverse_geocode((row['potential_aed_lat'], row['potential_aed_lon']))
    
    # Extract province from the result
    for component in result[0]['address_components']:
        if 'administrative_area_level_1' in component['types']:
            province = component['long_name']
            return province

    return "Province Not Found"

def add_province_to_comparisons():
    cluster = pd.read_csv(COMPARE_PATH / 'new_aeds_grid__old_aeds.csv')
    grid = pd.read_csv(COMPARE_PATH / 'new_aeds_cluster__old_aeds')

    cluster['Province'] = cluster.apply(get_province, axis=1)
    grid['Province'] = grid.apply(get_province, axis=1)

    # Define the replacements
    replacements = {
        "Vlaams Gewest": "Flanders",
        "Région Wallonne": "Wallonia",
        "Waals Gewest": "Wallonia",
        "Bruxelles": "Brussels"
    }

    # Apply the replacements to the "Province" column
    cluster['Province'] = cluster['Province'].replace(replacements)
    grid['Province'] = grid['Province'].replace(replacements)

    # Save the modified datasets back to CSV files (if needed)
    cluster.to_csv(COMPARE_PATH / 'new_aeds_grid__old_aeds__with_province.csv', index=False)
    grid.to_csv(COMPARE_PATH / 'new_aeds_cluster__old_aeds__with_province.csv', index=False)

if __name__ == '__main__':
    add_province_to_comparisons()
