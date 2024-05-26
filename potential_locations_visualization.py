import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="aed_locator")

# Function to reverse geocode coordinates to an address
def reverse_geocode(lat, lon):
    location = geolocator.reverse((lat, lon))
    if location:
        return location.address
    else:
        return "Address not found"
    
def show_potential_locations_visualization():

    st.title("The top 80 optimal potential AEDs location")
    st.write("""Tick on the box if you also want to see the interventions they optimiza and the nearest existing AED""")

    # Load the grouped interventions data
    grouped_interventions = pd.read_csv("./transformed_data/interventions_closest_to_potential_aeds.csv")
    
    # Filter the top 50 potential AEDs by arrest_count
    optimal_potential_aeds = grouped_interventions.nlargest(50, 'arrest_count')
    
    # Convert stringified lists to actual lists
    optimal_potential_aeds['intervention_lat'] = optimal_potential_aeds['intervention_lat'].apply(eval)
    optimal_potential_aeds['intervention_lon'] = optimal_potential_aeds['intervention_lon'].apply(eval)
    optimal_potential_aeds['existing_aed_lat'] = optimal_potential_aeds['existing_aed_lat'].apply(eval)
    optimal_potential_aeds['existing_aed_lon'] = optimal_potential_aeds['existing_aed_lon'].apply(eval)
    optimal_potential_aeds['intervention_id'] = optimal_potential_aeds['intervention_id'].apply(eval)
    optimal_potential_aeds['existing_aed_id'] = optimal_potential_aeds['existing_aed_id'].apply(eval)
    
    # Create a map centered around the mean coordinates of the interventions
    m = folium.Map(location=(50.8798, 4.7005), zoom_start=8)
    
    # Checkboxes for user to select which markers to display
    show_interventions = st.checkbox('Show Optimized Interventions', value=False)
    show_existing_aeds = st.checkbox('Show Nearest Exsting AEDs', value=False)
    
    # Add markers based on user selection
    for _, row in optimal_potential_aeds.iterrows():
        # Create popup content for potential AEDs
        intervention_ids = ', '.join(map(str, row['intervention_id']))
        address = reverse_geocode(row['potential_aed_lat'], row['potential_aed_lon'])
        popup_content = f"Potential AED ID: {row['potential_aed_id']}<br>Arrest Count: {row['arrest_count']}<br>Closest Interventions: {intervention_ids}"
        folium.Marker(
            location=[row['potential_aed_lat'], row['potential_aed_lon']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

    if show_interventions:
        for _, row in optimal_potential_aeds.iterrows():
            for lat, lon, intervention_id, existing_aed_id in zip(row['intervention_lat'], row['intervention_lon'], row['intervention_id'], row['existing_aed_id']):
                address = reverse_geocode(lat, lon)
                # Create popup content for interventions
                popup_content = f"Intervention ID: {intervention_id}<br>Closest Existing AED ID: {existing_aed_id}"
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color='red', icon='heart')
                ).add_to(m)

    if show_existing_aeds:
        for _, row in optimal_potential_aeds.iterrows():
            for lat, lon, existing_aed_id in zip(row['existing_aed_lat'], row['existing_aed_lon'], row['existing_aed_id']):
                address = reverse_geocode(lat, lon)
                popup_content = f"Existing AED ID: {existing_aed_id}"
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color='blue', icon='flash')
                ).add_to(m)

    # Display map in Streamlit
    folium_static(m)
    