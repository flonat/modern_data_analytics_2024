import streamlit as st
from data_exploration import show_data_exploration
from potential_aed_locations import show_potential_locations 
from potential_locations_visualization import show_potential_locations_visualization
from comparing_algos import show_compare_algos
from logistic_regression import logistic_regression

# Set the path to your data directory
data_directory = "./data"

data_exploration, possible_locations, viz, logistics = st.tabs([
    "Data Exploration", 
    "Possible locations", 
    "Visualization", 
    "Predict patient survival from waiting time"
    ])

with data_exploration:
    show_data_exploration(data_directory)

with possible_locations:
    show_potential_locations()

with viz:
    show_potential_locations_visualization()

with logistics:
    logistic_regression()


