import googlemaps
import pyarrow.parquet as pq
import pandas as pd
import os
from paths import DATA_PATH, INFORMATION_PATH, LOCATION_PATH

GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)  

def get_lat_lon(address):
    # Geocode an address
    result = gmaps.geocode(address)

    # If result is not empty, extract latitude and longitude
    if result:
        location = result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        return None, None

def extract_aed_locations():
    # Load the AED locations data
    aed_locations = pq.ParquetFile(DATA_PATH / 'aed_locations.parquet.gzip').read().to_pandas()

    # Get AED full addresses
    aed_addresses = []
    for index, location in aed_locations.iterrows():
        number = '' if pd.isnull(location['number']) else location['number']
        postal_code = '' if pd.isnull(location['postal_code']) else int(location['postal_code'])
        address = f'{number} {location['address']}, {location['municipality']}, {location['province']}, Belgium {postal_code}'
        aed_addresses.append(address)

    aed_locations['full_address'] = aed_addresses

    # Drop duplicate addresses
    aed_locations = aed_locations.drop_duplicates(subset=['full_address'])

    # Get latitude and longitude for each AED location
    aed_lats = []
    aed_lons = []

    for address in aed_locations['full_address']:
        lat, lon = get_lat_lon(address)
        aed_lats.append(lat)
        aed_lons.append(lon)

    aed_locations['lat'] = aed_lats
    aed_locations['lon'] = aed_lons

    # Save the arrests data to a CSV file
    aed_locations.to_csv(INFORMATION_PATH / 'old_aeds.csv', index=False)

    # Save the AED locations data
    aed_locations.to_csv(LOCATION_PATH / 'old_aeds.csv', index=False)


if __name__ == '__main__':
    extract_aed_locations()