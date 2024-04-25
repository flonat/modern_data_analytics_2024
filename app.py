import streamlit as st
from data_exploration import show_data_exploration
from potential_aed_locations import show_potential_locations 

# Set the path to your data directory
data_directory = "./data"

tab1, tab2 = st.tabs(["Data Exploration", "Possible locations"])

with tab1:
    show_data_exploration(data_directory)

with tab2:
    show_potential_locations()



