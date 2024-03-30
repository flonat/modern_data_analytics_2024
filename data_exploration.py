import streamlit as st
import pyarrow.parquet as pq
import pandas as pd
import os

def show_data_exploration(data_directory):
    # Get a list of all the gzipped Parquet files in the data directory
    parquet_files = [f for f in os.listdir(data_directory) if f.endswith('.parquet.gzip')]

    # Let the user select a file
    selected_file = st.selectbox('Select a file', parquet_files)

    # Open the selected Parquet file
    parquet_file = pq.ParquetFile(os.path.join(data_directory, selected_file))

    # Read the data from the Parquet file
    table = parquet_file.read()

    # Convert the table to a pandas DataFrame
    df = table.to_pandas()

    st.write("Data Types of Each Column:", df.dtypes)

    # After the DataFrame is loaded, get the list of columns
    columns = df.columns.tolist()

    # Let the user select a column from the loaded DataFrame
    selected_column = st.selectbox('Select a column', columns)

    # Display the distinct values of the selected column
    if selected_column:
        distinct_values = df[selected_column].dropna().unique()
        distinct_values.sort()
        st.write(f"Distinct values in '{selected_column}':", distinct_values)

    # Add a search input field for the user to enter a search term
    search_term = st.text_input("Enter a search term to filter the data")

    # Filter the DataFrame based on the search term and the selected column
    if search_term:
        filtered_df = df[df[selected_column].astype(str).str.contains(search_term, case=False)]
    else:
        filtered_df = df

    # Display the data types of each column in the DataFrame

    # Display the filtered DataFrame
    st.write(filtered_df)

    if selected_file == 'interventions_bxl2.parquet.gzip':
        # Iterate over each row to display a button on the map for each intervention
        # Prepare a DataFrame to hold all latitude and longitude values
        map_data = pd.DataFrame(columns=['lat', 'lon'])
        show_cardiac_incidences = st.radio("Show cardiac related incidences", ('Yes', 'No'), index=0)
        # Iterate over the first 20 rows to collect latitude and longitude
        for index, row in df.iterrows():
            current_longitude = row["Longitude intervention"]
            current_latitude = row["Latitude intervention"]
            if pd.isnull(current_longitude) or pd.isnull(current_latitude):
                continue
            current_longitude, current_latitude = format_coordinates(row["Longitude intervention"], row["Latitude intervention"])
            if show_cardiac_incidences == 'Yes':
                cardiac_arrest_event_types = [
                    'HARTSTILSTAND - DOOD - OVERLEDEN',
                    'PIJN OP DE BORST',
                    'CARDIAAL PROBLEEM (ANDERE DAN PIJN AAN DE BORST)'
                ]
                is_interesting = any(event_type in row["EventType and EventLevel"] for event_type in cardiac_arrest_event_types) if row["EventType and EventLevel"] else False
                if is_interesting:
                    # Append the current latitude and longitude to the map_data DataFrame
                    map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)
            else:
                # Append the current latitude and longitude to the map_data DataFrame without filtering for cardiac incidences
                map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)

        # Plot all collected points on a single map
        if not map_data.empty:
            st.map(map_data)
    elif selected_file == 'interventions_bxl.parquet.gzip':
        cardiac_arrest_event_types = [
            'P003 - Cardiac arrest',
            'P019 - Unconscious - syncope',
            'P011 - Chest pain',
            'P029 - Obstruction of the respiratory tract',
            'P014 - Electrocution - electrification',
            'TI (3.3.1) rescue electrocution/electrification'
        ]
        map_data = pd.DataFrame(columns=['lat', 'lon'])
        show_cardiac_incidences = st.radio("Show cardiac related incidences", ('Yes', 'No'), index=0)
        # Iterate over the first 20 rows to collect latitude and longitude
        for index, row in df.iterrows():
            current_longitude = row["longitude_intervention"]
            current_latitude = row["latitude_intervention"]
            if pd.isnull(current_longitude) or pd.isnull(current_latitude):
                continue
            current_longitude, current_latitude = format_coordinates(row["longitude_intervention"], row["latitude_intervention"])
            if show_cardiac_incidences == 'Yes':
                is_interesting = any(event_type in row["eventtype_trip"] for event_type in cardiac_arrest_event_types) if row["eventtype_trip"] else False
                if is_interesting:
                    # Append the current latitude and longitude to the map_data DataFrame
                    map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)
            else:
                # Append the current latitude and longitude to the map_data DataFrame without filtering for cardiac incidences
                map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)

        # Plot all collected points on a single map
        if not map_data.empty:
            st.map(map_data)




def format_coordinates(longitude, latitude):
    formatted_longitude = str(longitude)[:1] + '.' + str(longitude).replace('.', '')[1:]
    formatted_latitude = str(latitude)[:2] + '.' + str(latitude).replace('.', '')[2:]
    return formatted_longitude, formatted_latitude