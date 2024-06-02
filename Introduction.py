import streamlit as st

st.set_page_config(layout='wide',
                   page_title="Introduction",
)

st.title('Introduction')
st.write("""
In this project, we aimed to analyze the impact of time-to-hospital on patient survival rates, particularly in the context of cardiac arrests. Our approach involved several steps:

1. **Find potential new AED locations**: We identified potential locations for Automated External Defibrillators (AEDs) via 2 approaches: a naive grid-based approach and a more sophisticated clustering approach. 

2. **Evaluate potential new AED locations**: We visualized the potential AED locations for each approach and compared the two approaches by number of arrests having shorter distance to the closest AED under each approach.

3. **Predict patient survival from waiting time**: We modeled the relationship between waiting time and survival rate using logistic regression in order to determine whether having shorter waiting time for medical intervention could help increase the survival rate. However, we found that survival rates paradoxically decreased with longer waiting times, even when controlled by other variables.

Despite the unexpected results from the logistic regression model, this project provided valuable insights into the factors affecting patient survival rates and the potential benefits of strategically placed AEDs. It also highlighted the importance of considering hidden variables when interpreting the results of statistical models.
""")

