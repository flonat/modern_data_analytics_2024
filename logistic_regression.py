import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import folium_static
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, recall_score
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scripts.paths import INFORMATION_PATH

st.set_page_config(layout='wide')
st.title('Predict patient survival from waiting time using logistic regression')

@st.cache_data
def load_data():
    ts_cols = ['t0', 't1', 't1confirmed', 't2', 't3', 't4', 't5', 't6', 't7', 't9']
    arrests = pd.read_csv(INFORMATION_PATH / 'arrests.csv', parse_dates=ts_cols, date_format='ISO8601')
    return arrests

def logistic_regression():
    data_load_state = st.text('Loading data...')
    arrests = load_data()
    data_load_state.text('Loading data...done!')
    # categorical_cols = arrests.select_dtypes(include='object').columns
    categorical_cols = ['no_control', 'vector_type', 'eventtype_trip', 'severity', 'cityname_intervention', 'province_intervention']

    control = st.selectbox(
        'Control variable',
        categorical_cols)
    
    col1, col2 = st.columns(2)
    
    with col1:
        death_weight = st.slider('Relative weight of deaths', 1, 40, 20)
    with col2:
        n_top_categories = st.slider('Number of top categories to display', 1, 10, 5)

    arrests_filtered = arrests[['waiting_time_combined', control, 'survived']].dropna()
    X = arrests_filtered[['waiting_time_combined', control]]
    X = pd.get_dummies(X, columns=[control], drop_first=True)
    y = arrests_filtered['survived']

    # Preprocess the data by imputing missing values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Scale waiting_time_combined in X_train and X_test within the range [0, 1]

    # Define the class weights
    class_weights = {0: death_weight, 1: 1}

    # Create the classifier with class weights
    model = LogisticRegression(class_weight=class_weights, max_iter=300)

    # Fit the classifier to your data
    model.fit(X_train, y_train)

    # Predict the target variable for the test set
    y_pred = model.predict(X_test)
    
    # Calculate death recall of the model
    death_recall = recall_score(y_test, y_pred, pos_label=False) 

    # Compute the confusion matrix
    display_labels = ['Survived' if model_class else 'Dead' for model_class in model.classes_]
    disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_test, y_pred, labels=model.classes_), display_labels=display_labels)

    # Print model odds
    waiting_time_coef = model.coef_[0][0]
    st.write(f'A 10-minute increase in waiting time increases the survival odds by {np.exp(waiting_time_coef*10):.2f} times')
    col4, col5 = st.columns([0.25, 0.75])

    with col4:
        # Display death recall
        st.header(f'Death recall')
        st.subheader(f'{round(death_recall*100, 1)}%')

        # Plot confusion matrix
        fig1, ax = plt.subplots()
        disp.plot(ax=ax)
        st.pyplot(fig1)

    # Calculate actual survival percentage for each group of (rounded) waiting time & control
    arrests_plotted = arrests_filtered.copy()
    arrests_plotted['waiting_time_combined'] = arrests_plotted['waiting_time_combined'].round()
    survival_percentages = arrests_plotted.groupby(['waiting_time_combined', control], as_index=False)['survived'].agg(['count', 'mean', 'sum'])
    survival_percentages = survival_percentages.rename(columns={'count': 'count', 'mean': 'actual_percentage', 'sum': 'survived'})
    survival_percentages['actual_percentage_std'] = np.sqrt(survival_percentages['actual_percentage'] * (1-survival_percentages['actual_percentage']) / survival_percentages['count']) * 100
    survival_percentages['actual_percentage'] = survival_percentages['actual_percentage'] * 100

    # Predict the survival probability for each control group
    survival_percentages[f'{control}_copy'] = survival_percentages[control].copy()
    survival_percentages = pd.get_dummies(survival_percentages, columns=[control], drop_first=True)
    survival_percentages.rename(columns={f'{control}_copy': control}, inplace=True)
    survival_percentages['predicted_percentage'] = model.predict_proba(survival_percentages[X.columns])[:, 1] * 100

    # Plot all categories in the same chart, with different colors

    fig2 = go.Figure()
    top_categories = survival_percentages.groupby(control)['count'].sum().sort_values(ascending=False).index[:n_top_categories]
    top_arrests_plotted = arrests_plotted[arrests_plotted[control].isin(top_categories)]
    top_survival_percentages = survival_percentages[survival_percentages[control].isin(top_categories)]
    top_survival_percentages[control] = pd.Categorical(top_survival_percentages[control], categories=top_categories[::-1], ordered=True)
    

    colors = {}
    
    for i, category in enumerate(top_categories):
        category_data = top_survival_percentages[top_survival_percentages[control] == category]
        
        # Generate a unique color for each category if not already generated
        if category not in colors:
            colors[category] = 'rgba({},{},{},1)'.format(*(np.random.RandomState(i).randint(0, 255, size=3)))
        
        # Create the scatter plot for the actual survival percentages with tooltips
        scatter = go.Scatter(
            x=category_data['waiting_time_combined'],
            y=category_data['actual_percentage'],
            mode='markers',
            name=f'Actual - {category}',
            text=[
                f"Actual: {row['actual_percentage']:.2f}% ± {row['actual_percentage_std']:.2f}%<br>Predicted: {row['predicted_percentage']:.2f}%<br>Count: {row['count']}"
                for i, row in category_data.iterrows()
            ],
            hoverinfo='text',
            marker=dict(color=colors[category])
        )

        # Create the line plot for the predicted survival percentages
        line = go.Scatter(
            x=category_data['waiting_time_combined'],
            y=category_data['predicted_percentage'],
            mode='lines',
            name=f'Predicted - {category}',
            line=dict(color=colors[category]),
        )

        # Add the scatter and line plot to the figure
        fig2.add_trace(scatter)
        fig2.add_trace(line)

    # Set the titles and labels
    fig2.update_layout(
        title='Percentage of Survival by Waiting Time',
        xaxis_title='Waiting Time (minutes)',
        yaxis_title='Percentage of Survival',
        template='plotly_white',
        xaxis=dict(range=[0, 200])
    )
    with col5:
        st.plotly_chart(fig2, use_container_width=True)

    col6, col7, col8 = st.columns(3)
    with col6:
        # Plot horizontal bar chart of total number of arrests per control category using top_survival_percentages dataframe
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(
            x=top_survival_percentages.groupby(control)['count'].sum(),
            y=top_survival_percentages.groupby(control)['count'].sum().index,
            orientation='h',
            marker=dict(color='gray')
        ))
        fig6.update_layout(
            title='Total Number of Arrests per Control Category',
            xaxis_title='Number of Arrests',
            yaxis_title='Control Category',
            template='plotly_white'
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col7:
        # Plot horizontal bar chart of average waiting time per control category using top_survival_percentages dataframe
        fig7 = go.Figure()
        fig7.add_trace(go.Bar(
            x=top_arrests_plotted.groupby(control)['waiting_time_combined'].mean(),
            y=top_arrests_plotted.groupby(control)['waiting_time_combined'].mean().index,
            orientation='h',
            marker=dict(color='RoyalBlue')
        ))
        fig7.update_layout(
            title='Average Waiting Time per Control Category',
            xaxis_title='Average Waiting Time (minutes)',
            yaxis_title='Control Category',
            template='plotly_white'
        )
        st.plotly_chart(fig7, use_container_width=True)

    with col8:
        # PLot horizontal bar chart of average survival percentage per control category using top_survival_percentages dataframe
        fig8 = go.Figure()
        fig8.add_trace(go.Bar(
            x=top_arrests_plotted.groupby(control)['survived'].mean() * 100,
            y=top_arrests_plotted.groupby(control)['survived'].mean().index,
            orientation='h',
            marker=dict(color='MediumSeaGreen')
        ))
        fig8.update_layout(
            title='Survival Percentage per Control Category',
            xaxis_title='Survival Percentage (%)',
            yaxis_title='Control Category',
            template='plotly_white'
        )
        st.plotly_chart(fig8, use_container_width=True)


if __name__ == '__main__':
    logistic_regression()

