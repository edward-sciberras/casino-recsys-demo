import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image

# Load your game data
game_data = pd.read_json('game_data.json') 

def load_image(url):
    try:
        response = requests.get("https:" + url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image from {url}: {e}")
        return None

def main():
    st.title("Game Recommendations")

    selected_game = st.selectbox("Select a game", [""] + list(game_data['GameName']))

    if selected_game:
        st.subheader(f"Because You Played {selected_game}")
        
        recommendations = game_data[game_data['GameName'] == selected_game]['Recommendations'].iloc[0]
        recommendations = eval(recommendations) if isinstance(recommendations, str) else recommendations
        
        cols = st.columns(4)
        for i, url in enumerate(recommendations[:4]):
            img = load_image(url)
            if img:
                cols[i].image(img, use_column_width=True)
    else:
        st.subheader("Because You Played")

if __name__ == "__main__":
    main()