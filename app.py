import streamlit as st
import pandas as pd
import json
import requests
from PIL import Image
from io import BytesIO
import streamlit_authenticator as stauth
    
# Set page to wide mode
st.set_page_config(layout="wide")

# Function to add vertical space
def add_vertical_space(num_lines=1):
    for _ in range(num_lines):
        st.markdown('<br>', unsafe_allow_html=True)
    
# Access the secrets via the st.secrets dict
credentials = {
    "usernames": {
        "xibby": {
            "email": st.secrets["credentials"]["usernames"]["xibby"]["email"],
            "failed_login_attempts": st.secrets["credentials"]["usernames"]["xibby"]["failed_login_attempts"],
            "logged_in": st.secrets["credentials"]["usernames"]["xibby"]["logged_in"],
            "name": st.secrets["credentials"]["usernames"]["xibby"]["name"],
            "password": st.secrets["credentials"]["usernames"]["xibby"]["password"]
        }
    }
}

cookie_name = st.secrets["cookie"]["name"]
cookie_key = st.secrets["cookie"]["key"]
cookie_expiry_days = st.secrets["cookie"]["expiry_days"]
pre_authorized = st.secrets["pre-authorized"]

# Initialize the authenticator
authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry_days,
    pre_authorized
)

authenticator.login()

if st.session_state["authentication_status"]:
    # Load the JSON data
    with open('games_recommendations.json') as f:
        data = json.load(f)

    # Load the CSV data
    csv_path = 'demo-simple-data.csv'
    df = pd.read_csv(csv_path)

    # Replace null values with medians
    columns_to_fill = ['Betways']

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
    game_names = [item['GameName'] for item in data]

    # Define color map for similar features
    color_map = {
        'RTP': 'background-color: yellow',
        'Betways': 'background-color: lightgreen',
        'Volatility': 'background-color: orange',
        'Hitrate': 'background-color: lightpink',
        'Other': 'background-color: lightcoral'
    }
    
    # Function to highlight similar features in the selected game row
    def highlight_features(s, features):
        styles = pd.Series('', index=s.index)
        for feature in features:
            if feature in s.index:
                styles[feature] = color_map.get(feature, 'background-color: lightcoral')
        return styles

    # Function to highlight recommendation rows
    def highlight_recommendations(row, ids, sim_feats):
        styles = pd.Series('', index=row.index)
        if row['GameID'] in ids:
            idx = ids.index(row['GameID'])
            features = sim_feats[idx]
            for feature in features:
                if feature in row.index:
                    styles[feature] = color_map.get(feature, 'background-color: lightcoral')
        return styles
    
    def resize_image(img, target_size=(376, 250)):
        """Resize image to target size while maintaining aspect ratio"""
        img.thumbnail(target_size)
        background = Image.new('RGBA', target_size, (255, 255, 255, 0))
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        background.paste(img, offset)
        return background

    # Streamlit app
    st.title("Game Recommendations")

    # Dropdown menu for game selection
    selected_game = st.selectbox("Select a Game", game_names)
    
    # Find the selected game data
    selected_game_data = next((game for game in data if game['GameName'] == selected_game), None)

    if selected_game_data:
        # Create two columns: one for the selected game, one for recommendations
        col1, col2 = st.columns([1, 2])

        with col1:
            # Display the selected game image
            st.subheader("Selected Game")
            selected_game_url = selected_game_data.get('GameImageURL')
            if selected_game_url:
                response = requests.get("https:" + selected_game_url)
                img = Image.open(BytesIO(response.content))
                st.image(img, use_column_width=True)
            else:
                st.write("No image available for this game.")

        with col2:
            st.subheader("Recommendations")
            # Display recommendations in a 5x3 grid
            image_urls = selected_game_data.get('RecommendationsURLs', [])[:14]
            rows = 3
            cols = 5
            for i in range(rows):
                row_cols = st.columns(cols)
                for j in range(cols):
                    img_index = i * cols + j
                    if img_index < len(image_urls):
                        url = image_urls[img_index]
                        if url:
                            response = requests.get("https:" + url)
                            img = Image.open(BytesIO(response.content))
                            img_resized = resize_image(img)
                            row_cols[j].image(img_resized, use_column_width=True)
                            
        add_vertical_space(3)

        def get_column_config(df):
            config = {
                "GameID": None,
                "order": None
            }
            
            config.update({
                col: st.column_config.Column(width="auto") 
                for col in df.columns 
                if col not in ['GameID', 'order']
            })
            
            return config

        # Display the dataframe with the selected game's row with highlighted features
        st.subheader("Selected Game Details")
        selected_game_row = df[df['Name'] == selected_game].drop(columns=['GameID'])
        if not selected_game_row.empty:
            selected_game_styled = selected_game_row.style.apply(highlight_features, features=[item for sublist in selected_game_data['SimilarFeatures'] for item in sublist], axis=1)
            st.dataframe(
                selected_game_styled,
                hide_index=True,
                column_config=get_column_config(selected_game_row)
            )

        # Display the recommendations dataframe with highlighted features
        st.subheader("Recommendations and Features")
        recommendation_ids = selected_game_data.get('RecommendationsIDs', [])
        recommendation_rows = df[df['GameID'].isin(recommendation_ids)]
        if not recommendation_rows.empty:
            # Create a categorical column based on the order of RecommendationsIDs
            recommendation_rows['order'] = pd.Categorical(
                recommendation_rows['GameID'], 
                categories=recommendation_ids, 
                ordered=True
            )
            
            # Sort the dataframe based on this new column
            recommendation_rows = recommendation_rows.sort_values('order')
            
            recommendation_styled = recommendation_rows.style.apply(
                highlight_recommendations,
                ids=recommendation_ids,
                sim_feats=selected_game_data['SimilarFeatures'],
                axis=1
            )
        height = len(recommendation_rows) * 35 + 38
        st.dataframe(
            recommendation_styled,
            hide_index=True,
            height=height,
            column_config=get_column_config(recommendation_rows)
        )
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')


