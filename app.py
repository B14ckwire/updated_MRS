import pickle
import streamlit as st
import requests
import pandas as pd
from streamlit.components.v1 import html


# Custom CSS for better movie card styling
def inject_custom_css():
    st.markdown("""
    <style>
    .movie-card {
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        background: #1a1a1a;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
        height: 100%;
    }
    .movie-card:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
.movie-poster {
    width: 100%;
    height: 260px;
    object-fit: contain; /* Or 'scale-down' if you want the original size inside the box */
    border-radius: 8px;
    margin-bottom: 10px;
    display: block;
    background-color: #000; /* In case there's empty space around */
}


    .movie-title {
        font-weight: bold;
        color: white;
        font-size: 16px;
        text-align: center;
        margin-bottom: 5px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .recommendations-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        padding: 10px;
    }
    @media (max-width: 600px) {
        .recommendations-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    </style>
    """, unsafe_allow_html=True)


# Function to fetch movie poster (only for Hollywood)
def fetch_poster(movie_id, industry):
    if industry == 'Bollywood':
        return None  # No posters for Bollywood

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        return None
    except requests.exceptions.RequestException:
        return None


# Function to recommend movies (unchanged)
def recommend(movie, similarity_data, category_type, movies_df, industry):
    recommended_movies = []

    if industry == 'Hollywood':
        if category_type == 'Popularity-based':
            if movie not in similarity_data.index:
                st.error("Movie not found in popularity similarity data.")
                return []
            distances = similarity_data.loc[movie].astype(float)
            similar_titles = distances.sort_values().index[1:11]

            for title in similar_titles:
                movie_id = movies_df[movies_df['title'] == title].iloc[0].movie_id
                poster = fetch_poster(movie_id, industry)
                recommended_movies.append({'title': title, 'poster': poster})
        else:
            index = movies_df[movies_df['title'] == movie].index[0]
            distances = sorted(list(enumerate(similarity_data[index])), reverse=True, key=lambda x: x[1])
            for i in distances[1:11]:
                movie_id = movies_df.iloc[i[0]].movie_id
                poster = fetch_poster(movie_id, industry)
                recommended_movies.append({
                    'title': movies_df.iloc[i[0]].title,
                    'poster': poster
                })
    else:  # Bollywood
        if category_type == 'Released Year':
            try:
                target_year = movies_df[movies_df['title'] == movie].iloc[0]['year']
                year_movies = movies_df[movies_df['year'] == target_year]
                year_movies = year_movies[year_movies['title'] != movie]  # Exclude the selected movie

                if 'rating' in year_movies.columns:
                    year_movies = year_movies.sort_values('rating', ascending=False)

                for _, row in year_movies.head(10).iterrows():
                    recommended_movies.append({'title': row['title'], 'poster': None})
            except Exception as e:
                st.error(f"Error processing year-based recommendations: {e}")
                return []
        else:
            index = movies_df[movies_df['title'] == movie].index[0]
            distances = sorted(list(enumerate(similarity_data[index])), reverse=True, key=lambda x: x[1])
            for i in distances[1:11]:
                recommended_movies.append({
                    'title': movies_df.iloc[i[0]].title,
                    'poster': None
                })

    return recommended_movies


# Streamlit UI
st.set_page_config(layout="wide")  # Use wider layout
inject_custom_css()  # Inject our custom CSS

st.header('Konsa Movie Dekhoge? 🎬')

# Add toggle for Hollywood/Bollywood
movie_industry = st.radio("Select Movie Industry:", ('Hollywood', 'Bollywood'), horizontal=True)

# Load appropriate data based on selection
if movie_industry == 'Hollywood':
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    categories = ['Genre-based', 'Stars-based', 'Hybrid-based', 'Popularity-based']
    similarity_files = {
        'Genre-based': 'similarity2.pkl',
        'Stars-based': 'similarity1.pkl',
        'Hybrid-based': 'similarity0.pkl',
        'Popularity-based': 'popularity_similarity.pkl'
    }
else:
    movies = pickle.load(open('movie_list (1).pkl', 'rb'))
    categories = ['Genre-based', 'Stars-based']
    similarity_files = {
        'Genre-based': 'similarity2 (1).pkl',
        'Stars-based': 'similarity1 (1).pkl',
    }

# Category selection
category = st.radio("Select Recommendation Category:", categories, horizontal=True)

# Load similarity matrix (for all categories in both industries)
similarity = pickle.load(open(similarity_files[category], 'rb'))

# Movie selection dropdown
movie_list = movies['title'].values
selected_movie = st.selectbox(
    f"Type or select a {movie_industry} movie from the dropdown",
    movie_list
)

# Show recommendations
if st.button('Show Recommendation'):
    recommendations = recommend(selected_movie, similarity, category, movies, movie_industry)

    if not recommendations:
        st.warning("No recommendations found. Try a different movie or category.")
    elif movie_industry == 'Hollywood':
        # Display Hollywood movies with posters in a responsive grid
        st.markdown(f"<h3 style='text-align: center;'>Recommended Movies Similar to '{selected_movie}'</h3>",
                    unsafe_allow_html=True)

        # Create a grid layout
        st.markdown('<div class="recommendations-grid">', unsafe_allow_html=True)

        for movie in recommendations[:10]:
            poster = movie['poster'] if movie[
                'poster'] else "https://via.placeholder.com/500x750?text=Poster+Not+Available"
            st.markdown(f"""
            <div class="movie-card">
                <img src="{poster}" class="movie-poster" onerror="this.src='https://via.placeholder.com/500x750?text=Poster+Not+Available'">
                <div class="movie-title">{movie['title']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Display Bollywood movies as a list
        st.subheader(f"Recommended Bollywood Movies Similar to '{selected_movie}':")
        for i, movie in enumerate(recommendations[:10], 1):
            st.write(f"{i}. {movie['title']}")
