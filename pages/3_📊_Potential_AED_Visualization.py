import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import plotly.express as px
from scripts.paths import COMPARE_PATH

st.set_page_config(page_title="Potential AED Visualization", page_icon="🎯", layout='wide')

@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df


def show_potential_locations_visualization():
    st.title('Visualizing Optimal Potential AED Locations')

    st.write("""
This section provides a detailed explanation of the two methods used to identify optimal locations for Automated External Defibrillators (AEDs): a grid-based system and a clustering method.
1. Grid-based system: This approach divides the geographical area into a grid. Each grid point represents a potential AED location. The grid points with the highest number of cardiac arrests are considered as the optimal locations for potential AEDs. This method provides a straightforward, evenly distributed set of potential AED locations.
2. Clustering method: This approach identifies centers of gravity of cardiac arrest occurrences. It then ranks potential AED locations based on the number of cardiac arrests they can cover. This method allows for more targeted placement of AEDs in areas with higher incidences of cardiac arrests.

You can customize the number of potential AEDs they are looking for and choose the algorithm to use. The potential AED locations are displayed on a map for easy visualization. Each potential AED location is marked with a green icon, and the existing AEDs and intervention locations are also marked for reference. Users can click on the markers to get more information about each location.
Additionally, users can enter a specific potential AED ID to view the details of that location, including the number of cardiac arrests it can cover and the distances to the nearest intervention locations. They can also select a specific cardiac arrest ID to view the distances from that location to the existing and potential AEDs.
""")



    optimal_num = st.slider('How many potential AEDs you are looking for?', 50, 200, 50, step=50)
    algorithm = st.radio('Select the algorithm', ['Grid-based', 'Clustering'])

    # Load the grouped interventions data based on the selected algorithm
    if algorithm == 'Grid-based':
        grouped_interventions = pd.read_csv(COMPARE_PATH / "add_province_grid.csv")
    else:  # Clustering
        grouped_interventions = pd.read_csv(COMPARE_PATH / "add_province_gravity.csv")  # adjust this path to your clustering results

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
                        tooltip=f"Intervention ID: {intervention_id}",
                        icon=folium.Icon(color='red', icon='heart')
                    )
                )
            for lat2, lon2, existing_aed_id in zip(row['existing_aed_lat'], row['existing_aed_lon'], row['existing_aed_id']):
                fg.add_child(
                    folium.Marker(
                        location=[lat2, lon2],
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

    # Make a input box
    potential_aed_ids = optimal_potential_aeds['potential_aed_id']
    selected_potential_aed = st.selectbox('Enter your interested potential AED ID', list(potential_aed_ids))

    # Check if the input value is valid
    if selected_potential_aed not in optimal_potential_aeds['potential_aed_id'].values:
        st.warning("Please enter a valid potential AED ID, we still provide you the most optimal result:)")
        selected_potential_aed = int(optimal_potential_aeds['potential_aed_id'].iloc[0])
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
    
    # Display the map and Plotly chart in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st_folium(
            m,
            feature_group_to_add=nearest_intervention_fg,
            width=600,
            height=600,
            )
   
show_potential_locations_visualization()