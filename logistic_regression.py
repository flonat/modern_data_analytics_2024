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

st.title('Predict patient survival from waiting time using logistic regression')

@st.cache_data
def load_data():
    ts_cols = ['t0', 't1', 't1confirmed', 't2', 't3', 't4', 't5', 't6', 't7', 't9']
    arrests = pd.read_csv(INFORMATION_PATH / 'arrests.csv', parse_dates=ts_cols, date_format='ISO8601')

    arrests['eventlevel_trip_str'] = arrests['eventlevel_trip'].fillna(-1).astype(int).astype(str)
    arrests['travel_time'] = arrests['calculated_traveltime_destinatio'] / 60
    arrests['travel_time_ts'] = (arrests['t5'] - arrests['t4']).dt.total_seconds() / 60
    arrests['waiting_time_ts'] = (arrests['t3'] - arrests['t0']).dt.total_seconds() / 60
    arrests['care_time_ts'] = (arrests['t4'] - arrests['t3']).dt.total_seconds() / 60
    arrests['departure_time_ts'] = (arrests['t6'] - arrests['t1']).dt.total_seconds() / 60

    arrests['travel_time_combined'] = arrests['travel_time'].fillna(arrests['travel_time_ts'])
    arrests['waiting_time_combined'] = arrests['waiting_time'].fillna(arrests['waiting_time_ts'])

    arrests['waiting_time_combined'] = arrests['waiting_time_combined'].mask((arrests['waiting_time_combined'] < 0) | (arrests['waiting_time_combined'] > 2100))
    arrests['travel_time_combined'] = arrests['travel_time_combined'].mask((arrests['travel_time_combined'] < 0) | (arrests['travel_time_combined'] > 300))
    arrests['care_time_ts'] = arrests['care_time_ts'].mask((arrests['care_time_ts'] < 0) | (arrests['care_time_ts'] > 125))

    arrests['care_travel_time'] = arrests['care_time_ts'] + arrests['travel_time_combined']
    arrests['survived'] = ~arrests['abandon_reason'].isin(['overleden', 'dood ter plaatse'])

    arrests['no control'] = 'no control'
    return arrests

def logistic_regression():
    data_load_state = st.text('Loading data...')
    arrests = load_data()
    categorical_cols = list(arrests.select_dtypes('object_').columns)

    control = st.selectbox(
        "Control variable",
        categorical_cols)

    arrests_filtered = arrests[['waiting_time_combined', control, 'survived']].dropna()
    X = arrests_filtered[['waiting_time_combined', control]]
    X = pd.get_dummies(X, columns=[control], drop_first=True)
    y = arrests_filtered['survived']

    # Preprocess the data by imputing missing values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define the class weights
    class_weights = {0: 20, 1: 1}

    # Create the classifier with class weights
    model = LogisticRegression(class_weight=class_weights, max_iter=200)

    # Fit the classifier to your data
    model.fit(X_train, y_train)

    # Predict the target variable for the test set
    y_pred = model.predict(X_test)

    # Plot confusion matrix
    fig1, ax = plt.subplots()
    display_labels = ['Survived' if model_class else 'Dead' for model_class in model.classes_]
    disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_test, y_pred, labels=model.classes_), display_labels=display_labels)
    disp.plot(ax=ax)

    st.pyplot(fig1)

    # Display death recall
    death_recall = recall_score(y_test, y_pred, pos_label=False)
    st.write(f"Death recall: {round(death_recall*100, 1)}%")

    # Calculate actual survival percentage for each group of (rounded) waiting time & control
    arrests_plotted = arrests_filtered.copy()
    arrests_plotted['waiting_time_combined'] = arrests_plotted['waiting_time_combined'].round()
    survived_percentages = arrests_plotted.groupby(['waiting_time_combined', control], as_index=False)['survived'].agg(['count', 'mean'])
    survived_percentages = survived_percentages.rename(columns={'count': 'count', 'mean': 'actual_percentage'})
    survived_percentages['actual_percentage_std'] = np.sqrt(survived_percentages['actual_percentage'] * (1-survived_percentages['actual_percentage']) / survived_percentages['count']) * 100
    survived_percentages['actual_percentage'] = survived_percentages['actual_percentage'] * 100

    # Predict the survival probability for each control group
    survived_percentages[f'{control}_copy'] = survived_percentages[control].copy()
    survived_percentages = pd.get_dummies(survived_percentages, columns=[control], drop_first=True)
    survived_percentages.rename(columns={f'{control}_copy': control}, inplace=True)
    survived_percentages['predicted_percentage'] = model.predict_proba(survived_percentages[X.columns])[:, 1] * 100

    # Plot all categories in the same chart, with different colors
    fig2 = go.Figure()

    categories = survived_percentages[control].unique()

    colors = {}

    for i, category in enumerate(categories):
        category_data = survived_percentages[survived_percentages[control] == category]
        
        # Generate a unique color for each category if not already generated
        if category not in colors:
            colors[category] = 'rgba({},{},{},1)'.format(*(np.random.randint(0, 255, size=3)))
        
        # Create the scatter plot for the actual survival percentages with tooltips
        scatter = go.Scatter(
            x=category_data['waiting_time_combined'],
            y=category_data['actual_percentage'],
            mode='markers',
            name=f'Actual Survival Percentage - {category}',
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
            name=f'Logistic Regression Prediction - {category}',
            line=dict(color=colors[category])
        )

        # Add the scatter and line plot to the figure
        fig2.add_trace(scatter)
        fig2.add_trace(line)

    # Set the titles and labels
    fig2.update_layout(
        title='Percentage of Survived by Waiting Time',
        xaxis_title='Waiting Time (minutes)',
        yaxis_title='Percentage of Survived',
        template='plotly_white'
    )

    st.plotly_chart(fig2, use_container_width=True)


