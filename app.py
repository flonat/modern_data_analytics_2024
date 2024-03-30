import streamlit as st
from data_exploration import show_data_exploration

# Set the path to your data directory
data_directory = "./data"

tab1, tab2 = st.tabs(["Data Exploration", "Another Tab"])

with tab1:
    show_data_exploration(data_directory)

with tab2:
    st.write("Content for another tab goes here.")