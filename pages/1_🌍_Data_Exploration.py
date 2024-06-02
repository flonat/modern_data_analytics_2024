import streamlit as st
import pyarrow.parquet as pq
import pandas as pd
import os
from scripts.paths import LOCATION_PATH

st.set_page_config(page_title="Data Exploration", page_icon="🌍", layout='wide')
st.sidebar.header("Data Exploration")

@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

@st.cache_data
def load_parquet(file_path):
    df = pq.ParquetFile(file_path)
    return df

def format_coordinates(longitude, latitude):
    formatted_longitude = str(longitude)[:1] + '.' + str(longitude).replace('.', '')[1:]
    formatted_latitude = str(latitude)[:2] + '.' + str(latitude).replace('.', '')[2:]
    return formatted_longitude, formatted_latitude

def show_data_exploration(data_directory):
    st.title('🌍 Data Exploration')

    st.write('This tab is for data exploration and wrangling. It provides an interface to interact with the data. Users can select a file from the list of gzipped Parquet files. The selected file\'s data is loaded into a DataFrame. The DataFrame\'s columns are listed for selection. Users can select a column to view its unique values. A search input field is available for entering a term to filter the data based on the selected column.')

    # Get a list of all the gzipped Parquet files in the data directory
    parquet_files = [f for f in os.listdir(data_directory) if f.endswith('.parquet.gzip')]

    # Let the user select a file
    selected_file = st.selectbox('Select a file', parquet_files)

    # Open the selected Parquet file
    parquet_file = load_parquet(os.path.join(data_directory, selected_file))

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

     # Centralized file-specific configurations
    file_configs = {
        'interventions3.parquet.gzip': {
            'event_types': [
                "P003 - Cardiac arrest",
                "P014 - Electrocution - electrification",
                "P019 - Unconscious - syncope",
                "P011 - Chest pain"
            ],
            'columns': {
                'longitude': "Longitude intervention",
                'latitude': "Latitude intervention",
                'event': "EventType Trip"
            }
        },
        'interventions1.parquet.gzip': {
            'event_types': [
                "P003 - Cardiac arrest",
                "P014 - Electrocution - electrification",
                "P019 - Unconscious - syncope",
                "P011 - Chest pain"
            ],
            'columns': {
                'longitude': "Longitude intervention",
                'latitude': "Latitude intervention",
                'event': "EventType Trip"
            }
        },
        'interventions_bxl2.parquet.gzip': {
            'event_types': [
                'HARTSTILSTAND - DOOD - OVERLEDEN',
                'PIJN OP DE BORST',
                'CARDIAAL PROBLEEM (ANDERE DAN PIJN AAN DE BORST)'
            ],
            'columns': {
                'longitude': "Longitude intervention",
                'latitude': "Latitude intervention",
                'event': "EventType and EventLevel"
            }
        },
        'interventions_bxl.parquet.gzip': {
            'event_types': [
                'P003 - Cardiac arrest',
                'P019 - Unconscious - syncope',
                'P011 - Chest pain',
                'P029 - Obstruction of the respiratory tract',
                'P014 - Electrocution - electrification',
                'TI (3.3.1) rescue electrocution/electrification'
            ],
            'columns': {
                'longitude': "longitude_intervention",
                'latitude': "latitude_intervention",
                'event': "eventtype_trip"
            }
        }
    }

    # Common function to process and display map data
    def process_and_display_map_data(df, selected_file, show_cardiac_incidences):
        map_data = pd.DataFrame(columns=['lat', 'lon'])
        config = file_configs[selected_file]

        for index, row in df.iterrows():
            current_longitude = row[config['columns']['longitude']]
            current_latitude = row[config['columns']['latitude']]
            if pd.isnull(current_longitude) or pd.isnull(current_latitude):
                continue

            current_longitude, current_latitude = format_coordinates(current_longitude, current_latitude)

            if show_cardiac_incidences == 'Yes':
                is_interesting = any(event_type in row[config['columns']['event']] for event_type in config['event_types']) if row[config['columns']['event']] else False
                if is_interesting:
                    map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)
            else:
                map_data = pd.concat([map_data, pd.DataFrame({'lat': [float(current_latitude)], 'lon': [float(current_longitude)]})], ignore_index=True)

        if not map_data.empty:
            st.map(map_data)


    # Process and display map data based on the selected file
    if selected_file in file_configs:
        # Show cardiac incidences radio button
        show_cardiac_incidences = st.radio("Show cardiac related incidences", ('Yes', 'No'), index=0)
        process_and_display_map_data(df, selected_file, show_cardiac_incidences)
    
    st.divider()
    st.title('Results')
    st.write('After some cleanup we managed to create a consolided CSV of cardiac arrests')
    
    arrests_df = load_data(LOCATION_PATH / 'arrests.csv')

    # Assuming the DataFrame has 'latitude' and 'longitude' columns
    arrests_map_data = arrests_df[['lat', 'lon']]

    # Display the map
    st.map(arrests_map_data)
    




def format_coordinates(longitude, latitude):
    formatted_longitude = str(longitude)[:1] + '.' + str(longitude).replace('.', '')[1:]
    formatted_latitude = str(latitude)[:2] + '.' + str(latitude).replace('.', '')[2:]
    return formatted_longitude, formatted_latitude
    

data_directory = "./data"
show_data_exploration(data_directory)