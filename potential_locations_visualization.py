import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import folium_static

def show_potential_locations_visualization():
    # Load the grouped interventions data
    grouped_interventions = pd.read_csv("./transformed_data/interventions_closest_to_potential_aeds.csv")
    
    # Filter the top 80 potential AEDs by arrest_count
    top_potential_aeds = grouped_interventions.nlargest(50, 'arrest_count')
    
    # Convert stringified lists to actual lists
    top_potential_aeds['intervention_lat'] = top_potential_aeds['intervention_lat'].apply(eval)
    top_potential_aeds['intervention_lon'] = top_potential_aeds['intervention_lon'].apply(eval)
    top_potential_aeds['existing_aed_lat'] = top_potential_aeds['existing_aed_lat'].apply(eval)
    top_potential_aeds['existing_aed_lon'] = top_potential_aeds['existing_aed_lon'].apply(eval)
    
    # Create a map centered around the mean coordinates of the interventions
    center_lat = top_potential_aeds['aed_lat'].mean()
    center_lon = top_potential_aeds['aed_lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Add potential AED markers
    for _, row in top_potential_aeds.iterrows():
        folium.Marker(
            location=[row['aed_lat'], row['aed_lon']],
            popup=f"Potential AED ID: {row['potential_aed_id']}, Arrest Count: {row['arrest_count']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        # Add intervention markers
        for lat, lon in zip(row['intervention_lat'], row['intervention_lon']):
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='green', icon='heart')
            ).add_to(m)
        
        # Add existing AED markers
        for lat, lon in zip(row['existing_aed_lat'], row['existing_aed_lon']):
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='red', icon='flash')
            ).add_to(m)
    
    # Display map in Streamlit
    folium_static(m)



