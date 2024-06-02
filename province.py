import pandas as pd
import googlemaps

cluster = pd.read_csv('./transformed_data/compare/centers_of_gravity_potential_aed_locations__new_aeds_grid.csv')
grid = pd.read_csv('./transformed_data/compare/new_aeds_grid__old_aeds.csv')
# Replace 'YOUR_API_KEY' with your actual API key
gmaps = googlemaps.Client(key='your_googleAPI_key')

def get_province(row):
    # Perform reverse geocoding
    result = gmaps.reverse_geocode((row['potential_aed_lat'], row['potential_aed_lon']))
    
    # Extract province from the result
    for component in result[0]['address_components']:
        if 'administrative_area_level_1' in component['types']:
            province = component['long_name']
            return province

    return "Province Not Found"

# Apply reverse geocoding to each row and store the province information
cluster['Province'] = cluster.apply(get_province, axis=1)
grid['Province'] = grid.apply(get_province, axis=1)
