import streamlit as st
from data_exploration import show_data_exploration
from potential_aed_locations import show_potential_locations 
from potential_locations_visualization import show_potential_locations_visualization

# Set the path to your data directory
data_directory = "./data"

tab1, tab2, tab3= st.tabs(["Data Exploration", "Possible locations", "Visualization"])

with tab1:
    show_data_exploration(data_directory)

with tab2:
    show_potential_locations()

with tab3:
    show_potential_locations_visualization()


