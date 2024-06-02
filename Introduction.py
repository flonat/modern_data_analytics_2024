import streamlit as st

st.set_page_config(layout='wide',
                   page_title="Introduction",
)

st.title('Introduction')
st.write("""
In this project, we aimed to analyze the impact of time-to-hospital on patient survival rates, particularly in the context of cardiac arrests. Our approach involved several steps:

1. **Data Exploration & wrangling**: We started by exploring and wrangling the data. We joined multiple datasets to create a consolidated set of cardiac arrests. We also provided an interactive interface for users to select a file, a column from the loaded DataFrame, and a search term to filter the data. This allowed us to understand the structure and characteristics of our data better.

2. **Potential AED Locations**: We identified potential locations for Automated External Defibrillators (AEDs) to optimize response times. The locations were chosen based on factors such as proximity to high-risk areas and accessibility.

3. **Potential Locations Visualization**: We visualized the potential AED locations. This allowed us to interactively explore the potential AED locations, their proximity to interventions, and the impact of placing an AED at these locations.

4. **Logistic Regression**: We attempted to model the relationship between time-to-hospital and survival rate using logistic regression. We used various control variables and calculated survival percentages for different waiting times. However, the model did not perform as expected. We hypothesize that there isa hidden third variable that explained both the longer time to hospital and the survival rate, leading to a spurious correlation.

Despite the unexpected results from the logistic regression model, this project provided valuable insights into the factors affecting patient survival rates and the potential benefits of strategically placed AEDs. It also highlighted the importance of considering hidden variables when interpreting the results of statistical models.
""")

