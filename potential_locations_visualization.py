import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import plotly.express as px

def show_potential_locations_visualization():
    st.title("The top optimal potential AEDs location")
    # Move selection boxes to the sidebar
    optimal_num = st.slider('How many potential AEDs you are looking for?', 50, 200, 50, step=50)
    algorithm = st.radio('Select the algorithm', ['Grid-based', 'Clustering'])

    # Load the grouped interventions data based on the selected algorithm
    if algorithm == 'Grid-based':
        grouped_interventions = pd.read_csv("./transformed_data/compare/add_province_grid.csv")
    else:  # Clustering
        grouped_interventions = pd.read_csv("./transformed_data/compare/add_province_gravity.csv")  # adjust this path to your clustering results

    # Filter the top 50 potential AEDs by arrest_count
    optimal_potential_aeds = grouped_interventions.nlargest(optimal_num, 'arrest_count')
    st.write(f"**With a budget of {optimal_num} AEDs, {algorithm} algorithm shortens the distance to the closest AED for {optimal_potential_aeds['arrest_count'].sum()} cardiac arrests**")
   
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
    
    def center_of_map(selected_potential_aed, selected_intervention_id):
        if selected_intervention_id == '--':
            selected_aed_location = optimal_potential_aeds[optimal_potential_aeds['potential_aed_id'] == selected_potential_aed][['potential_aed_lat', 'potential_aed_lon']].values[0]
            return selected_aed_location
        elif selected_intervention_id != '--':
            intervention_index = selected_aed_data['intervention_id'].index(selected_intervention_id)
            intervention_lat1 = selected_aed_data['intervention_lat'][intervention_index]
            intervention_lon1 = selected_aed_data['intervention_lon'][intervention_index]
            intervention_location = (intervention_lat1, intervention_lon1)
            return intervention_location
    
    def zoom(selected_intervention_id):
        if selected_intervention_id == '--':
            return 15
        else:
            return 17

    # Display initial map in Streamlit
    selected_potential_aed = st.selectbox('Select your interested potential AED ID', ["--"] + list(optimal_potential_aeds['potential_aed_id']))
    if selected_potential_aed == "--":
        # Plotly scatter plot
        fig = px.scatter(
            optimal_potential_aeds, 
            x='Province', 
            y='arrest_count', 
            hover_data=['potential_aed_id'],
            labels={'arrest_count': 'Arrest Count', 'province': 'Province'},
            title='Hover over an AED point to get ID information',
            size='arrest_count',
            color='arrest_count',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(
            yaxis=dict(title='Arrest Count'),
            xaxis=dict(title='Province'),
            showlegend=False
        )
        fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
        return st.plotly_chart(fig)

    # Filter the data for the selected potential AED
    selected_aed_data = optimal_potential_aeds[optimal_potential_aeds['potential_aed_id'] == selected_potential_aed].iloc[0]
    arrest_count_output = selected_aed_data['arrest_count']
    st.write(f"**Great select! This potential AED location optimizes the distances from {arrest_count_output} intervention locations**")

    # Filter intervention IDs for the selected potential AED
    intervention_ids = selected_aed_data['intervention_id'] 
    selected_intervention_id = st.selectbox('Select your interested cardiac arrest ID.', ["--"] + list(intervention_ids))
    
    dynamic_center = center_of_map(selected_potential_aed, selected_intervention_id)
    dynamic_zoom = zoom(selected_intervention_id)
    nearest_intervention_fg = add_intervention_markers(selected_potential_aed)

    # Create a map centered around the location of the selected potential AED with adjusted zoom level
    m = folium.Map(location=dynamic_center, zoom_start=dynamic_zoom)

    # Add markers for potential AEDs
    for _, row in optimal_potential_aeds.iterrows():
        intervention_ids = ', '.join(map(str, row['intervention_id']))
        popup_content = f"Potential AED ID: {row['potential_aed_id']}<br>Arrest Count: {row['arrest_count']}<br>Province: {row['Province']}"
        folium.Marker(
            location=[row['potential_aed_lat'], row['potential_aed_lon']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

    if selected_intervention_id != '--':
        # Get the index of the selected intervention ID
        intervention_index = selected_aed_data['intervention_id'].index(selected_intervention_id)

        # Get the corresponding distances
        distance_to_existing_aed = selected_aed_data['distance_to_existing_aed'][intervention_index]
        distance_to_potential_aed = selected_aed_data['distance_to_potential_aed'][intervention_index]
        
        reduction = round((distance_to_existing_aed - distance_to_potential_aed) * 1000, 2)

        # Write the distance it saves
        st.write(f"**By setting the potential AED {selected_aed_data['potential_aed_id']}, we shorten {reduction} meters from your selected cardiac arrest location.**")

        # Get the coordinates for lines
        intervention_lat = selected_aed_data['intervention_lat'][intervention_index]
        intervention_lon = selected_aed_data['intervention_lon'][intervention_index]
        potential_aed_lat = selected_aed_data['potential_aed_lat']
        potential_aed_lon = selected_aed_data['potential_aed_lon']
        existing_aed_lat = selected_aed_data['existing_aed_lat'][intervention_index]
        existing_aed_lon = selected_aed_data['existing_aed_lon'][intervention_index]

        # Add lines to the map
        folium.PolyLine(
            locations=[[intervention_lat, intervention_lon], [potential_aed_lat, potential_aed_lon]],
            color='green',
            weight=2.5,
            opacity=1
        ).add_to(m)

        folium.PolyLine(
            locations=[[intervention_lat, intervention_lon], [existing_aed_lat, existing_aed_lon]],
            color='blue',
            weight=2.5,
            opacity=1
        ).add_to(m)

    # Display map in Streamlit
    out = st_folium(
        m,
        feature_group_to_add=nearest_intervention_fg,
        width=500,
        height=500,
    )
