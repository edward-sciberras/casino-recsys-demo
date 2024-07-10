import streamlit as st
import pandas as pd
import json
import requests
from PIL import Image
from io import BytesIO
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
    
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

authenticator.login()

if st.session_state["authentication_status"]:
    # Load the JSON data
    with open('games_recommendations.json') as f:
        data = json.load(f)

    # Load the CSV data
    csv_path = 'eda_cleaned_data.csv'
    df = pd.read_csv(csv_path)

    # Replace null values with medians
    columns_to_fill = ['RTP', 'Max Win', 'Betways', 'Volatility', 'Hitrate']

    # Calculate medians for the columns, handling Betways separately
    medians = {}
    for column in columns_to_fill:
        if column == 'Betways':
            # Filter only numerical values
            numeric_values = pd.to_numeric(df[column], errors='coerce')
            medians[column] = numeric_values.median()
        else:
            medians[column] = df[column].median()

    # Fill the null values with the calculated medians
    for column, median in medians.items():
        df[column].fillna(median, inplace=True)

    # Extract unique game names
    game_names = list({item['GameName'] for item in data})

    # Define color map for similar features
    color_map = {
        'RTP': 'background-color: yellow',
        'Max Win': 'background-color: lightblue',
        'Betways': 'background-color: lightgreen',
        'Volatility': 'background-color: orange',
        'Hitrate': 'background-color: lightpink'
    }

    # Streamlit app
    st.title("Game Recommendations")

    # Dropdown menu for game selection
    selected_game = st.selectbox("Select a Game", game_names)

    # Find the first instance of the selected game and get its image URLs
    selected_game_data = None
    image_urls = []
    recommendation_ids = []
    similar_features = []
    for game in data:
        if game['GameName'] == selected_game:
            selected_game_data = game
            image_urls = game['RecommendationsURLs'][:14]  # Get the first 14 URLs
            recommendation_ids = game['RecommendationsIDs']
            similar_features = game['SimilarFeatures']
            break

    # Display images in a 5x3 grid
    if image_urls:
        rows = 3
        cols = 5
        for i in range(rows):
            row_cols = st.columns(cols)
            for j in range(cols):
                img_index = i * cols + j
                if img_index < len(image_urls):
                    url = image_urls[img_index]
                    if url:  # Check if the URL is not empty
                        response = requests.get("https:" + url)
                        img = Image.open(BytesIO(response.content))
                        row_cols[j].image(img, use_column_width=True)
    else:
        st.write("No images available for this game.")

    # Filter the CSV dataframe for the selected game
    selected_game_row = df[df['Name'] == selected_game]

    # Function to highlight similar features in the selected game row
    def highlight_features(s, features):
        styles = pd.Series('', index=s.index)
        for feature in features:
            if feature in s.index:
                styles[feature] = color_map.get(feature, '')
        return styles

    # Display the dataframe with the selected game's row with highlighted features
    st.subheader("Selected Game Details")
    if not selected_game_row.empty:
        selected_game_styled = selected_game_row.style.apply(highlight_features, features=similar_features, axis=1)
        st.dataframe(selected_game_styled)

    # Filter the CSV dataframe for the recommendation IDs
    recommendation_rows = df[df['GameID'].isin(recommendation_ids)]

    # Function to highlight recommendation rows
    def highlight_recommendations(row, ids, sim_feats):
        styles = pd.Series('', index=row.index)
        if row['GameID'] in ids:
            idx = ids.index(row['GameID'])
            feature = sim_feats[idx]
            if feature in row.index:
                styles[feature] = color_map.get(feature, '')
        return styles

    # Display the recommendations dataframe with highlighted features
    st.subheader("Recommendations and Features")
    if not recommendation_rows.empty:
        recommendation_styled = recommendation_rows.style.apply(
            highlight_recommendations,
            ids=recommendation_ids,
            sim_feats=similar_features,
            axis=1
        )
        st.dataframe(recommendation_styled)
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')


