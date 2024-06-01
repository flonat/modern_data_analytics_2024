import streamlit as st
from data_exploration import show_data_exploration
from potential_aed_locations import show_potential_locations 
from potential_locations_visualization import show_potential_locations_visualization
from comparing_algos import show_compare_algos

# Set the path to your data directory
data_directory = "./data"

tab1, tab2, tab3, tab4 = st.tabs(["Data Exploration", "Possible locations", "Visualization", "Comparing two algos"])

with tab1:
    show_data_exploration(data_directory)

with tab2:
    show_potential_locations()

with tab3:
    show_potential_locations_visualization()

with tab4:
    show_compare_algos()


