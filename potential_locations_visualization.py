import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast

def show_potential_locations_visualization():

    st.title("The optimal potential AEDs location")

    # Load the grouped interventions data
    grouped_interventions = pd.read_csv("./transformed_data/compare/new_aeds_grid__old_aeds.csv")
    
    # Filter the top 50 potential AEDs by arrest_count
    optimal_potential_aeds = grouped_interventions.nlargest(50, 'arrest_count')
    
    # Convert stringified lists to actual lists
    optimal_potential_aeds['intervention_lat'] = optimal_potential_aeds['intervention_lat'].apply(eval)
    optimal_potential_aeds['intervention_lon'] = optimal_potential_aeds['intervention_lon'].apply(eval)
    optimal_potential_aeds['existing_aed_lat'] = optimal_potential_aeds['existing_aed_lat'].apply(eval)
    optimal_potential_aeds['existing_aed_lon'] = optimal_potential_aeds['existing_aed_lon'].apply(eval)
    optimal_potential_aeds['intervention_id'] = optimal_potential_aeds['intervention_id'].apply(eval)
    optimal_potential_aeds['existing_aed_id'] = optimal_potential_aeds['existing_aed_id'].apply(eval)
    optimal_potential_aeds['distance_to_existing_aed'] = optimal_potential_aeds['distance_to_existing_aed'].apply(ast.literal_eval)
    optimal_potential_aeds['distance_to_potential_aed'] = optimal_potential_aeds['distance_to_potential_aed'].apply(ast.literal_eval)

    # Define function to add markers for interventions
    def add_intervention_markers(selected_potential_aed):
        fg = folium.FeatureGroup(name="Nearest Interventions")
        nearest_intervention = optimal_potential_aeds[optimal_potential_aeds['potential_aed_id'] == selected_potential_aed]
        for _, row in nearest_intervention.iterrows():
            for lat1, lon1, intervention_id, existing_aed_id in zip(row['intervention_lat'], row['intervention_lon'], row['intervention_id'], row['existing_aed_id']):
                fg.add_child(
                    folium.Marker(
                        location=[lat1, lon1],
                        popup=f"Intervention ID: {intervention_id}<br>Closest Existing AED ID: {existing_aed_id}<br>Cloest Potential AED ID: {row['potential_aed_id']}",
                        tooltip=f"Intervention ID: {intervention_id}<br>Closest Existing AED ID: {existing_aed_id}<br>Cloest Potential AED ID: {row['potential_aed_id']}",
                        icon=folium.Icon(color='red', icon='heart')
                    )
                )
            for lat2, lon2, existing_aed_id in zip(row['existing_aed_lat'], row['existing_aed_lon'], row['existing_aed_id']):
                fg.add_child(
                    folium.Marker(
                        location=[lat2, lon2],
                        popup=f"Existing AED ID: {existing_aed_id}",
                        tooltip=f"Existing AED ID: {existing_aed_id}",
                        icon=folium.Icon(color='blue', icon='flash')
                    )
                )
        return fg
    
    def center_of_map(selected_potential_aed):
        selected_aed_location = optimal_potential_aeds[optimal_potential_aeds['potential_aed_id'] == selected_potential_aed][['potential_aed_lat', 'potential_aed_lon']].values[0]
        return selected_aed_location


    # Display initial map in Streamlit
    m1 = folium.Map(location=(optimal_potential_aeds['potential_aed_lat'].mean(), optimal_potential_aeds['potential_aed_lon'].mean()), zoom_start=8)
    for _, row in optimal_potential_aeds.iterrows():
        intervention_ids = ', '.join(map(str, row['intervention_id']))
        popup_content = f"Potential AED ID: {row['potential_aed_id']}"
        folium.Marker(
            location=[row['potential_aed_lat'], row['potential_aed_lon']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m1)
    selected_potential_aed = st.selectbox('Select your interested potential AED ID', ["--"] + list(optimal_potential_aeds['potential_aed_id']))
    if selected_potential_aed == "--":
        st.write('You may click on the green marker for details')
        return st_folium(m1, width=500, height=500)
    dynamic_center = center_of_map(selected_potential_aed)
    nearest_intervention_fg1 = add_intervention_markers(selected_potential_aed)

    # Create a map centered around the location of the selected potential AED with adjusted zoom level
    m = folium.Map(location=dynamic_center, zoom_start=15)

    # Filter the data for the selected potential AED
    selected_aed_data = optimal_potential_aeds[optimal_potential_aeds['potential_aed_id'] == selected_potential_aed].iloc[0]
    arrest_count_output = selected_aed_data['arrest_count']
    st.write(f"**Great select! This potential AED location optimize the distances from {arrest_count_output} intervention locations**")

    # Add markers for potential AEDs
    for _, row in optimal_potential_aeds.iterrows():
        intervention_ids = ', '.join(map(str, row['intervention_id']))
        popup_content = f"Potential AED ID: {row['potential_aed_id']}<br>Arrest Count: {row['arrest_count']}<br>Closest Interventions: {intervention_ids}"
        folium.Marker(
            location=[row['potential_aed_lat'], row['potential_aed_lon']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

    # Filter intervention IDs for the selected potential AED
    intervention_ids = selected_aed_data['intervention_id'] 
    selected_intervention_id = st.selectbox('Select your interested cardiac arrest ID. Click on red marker for info', intervention_ids)

    # Get the index of the selected intervention ID
    intervention_index = intervention_ids.index(selected_intervention_id)

    # Get the corresponding distances
    distance_to_existing_aed = selected_aed_data['distance_to_existing_aed'][intervention_index]
    distance_to_potential_aed = selected_aed_data['distance_to_potential_aed'][intervention_index]
    
    reduction = round((distance_to_existing_aed - distance_to_potential_aed) * 1000, 2)
    

    # Write the distance it saves
    st.write(f"**By setting the potential AED {selected_aed_data['potential_aed_id']}, we shorten {reduction} meters from this cardiac arrest location.**")
    
    # Display map in Streamlit
    out = st_folium(
        m,
        feature_group_to_add = nearest_intervention_fg1,
        width=500,
        height=500,
    )
