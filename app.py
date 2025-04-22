import pickle
import streamlit as st
import requests
import pandas as pd
from streamlit.components.v1 import html
import io
download_data = []

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
        object-fit: contain;
        border-radius: 8px;
        margin-bottom: 10px;
        display: block;
        background-color: #000;
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
        return None
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        return f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
    except requests.exceptions.RequestException:
        return None

# Recommendation logic
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
                recommended_movies.append({'title': movies_df.iloc[i[0]].title, 'poster': poster})
    else:
        if category_type == 'Released Year':
            try:
                target_year = movies_df[movies_df['title'] == movie].iloc[0]['year']
                year_movies = movies_df[movies_df['year'] == target_year]
                year_movies = year_movies[year_movies['title'] != movie]
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
                recommended_movies.append({'title': movies_df.iloc[i[0]].title, 'poster': None})
    return recommended_movies

# Streamlit UI
st.set_page_config(layout="wide")
inject_custom_css()

st.header('Konsa Movie Dekhoge? 🎬')

movie_industry = st.radio("Select Movie Industry:", ('Hollywood', 'Bollywood'), horizontal=True)

# Load appropriate data
if movie_industry == 'Hollywood':
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    tags_df = pd.read_csv('movie_tags.csv')
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

category = st.radio("Select Recommendation Category:", categories, horizontal=True)
similarity = pickle.load(open(similarity_files[category], 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    f"Type or select a {movie_industry} movie from the dropdown",
    movie_list
)

# ✅ Show tags for Hollywood movies
if movie_industry == 'Hollywood':
    movie_tags_row = tags_df[tags_df['title'] == selected_movie]
    if not movie_tags_row.empty:
        tags_text = movie_tags_row['tags'].values[0]
        st.markdown("#### 🏷️ Tags for selected movie:")
        st.markdown(
            f"<div style='color: #ddd; font-size: 16px; background-color: #111; padding: 10px; border-radius: 8px'>{tags_text}</div>",
            unsafe_allow_html=True
        )

# Show recommendations
if st.button('Show Recommendation'):
    recommendations = recommend(selected_movie, similarity, category, movies, movie_industry)
    if not recommendations:
        st.warning("No recommendations found. Try a different movie or category.")
    elif movie_industry == 'Hollywood':
        st.markdown(f"<h3 style='text-align: center;'>Recommended Movies Similar to '{selected_movie}'</h3>", unsafe_allow_html=True)
        st.markdown('<div class="recommendations-grid">', unsafe_allow_html=True)
        for movie in recommendations[:10]:
            title = movie['title']
            poster = movie['poster'] if movie[
                'poster'] else "https://via.placeholder.com/500x750?text=Poster+Not+Available"

            # Get tags for the recommended movie
            tag_row = tags_df[tags_df['title'].str.strip() == title.strip()]
            tags_text = tag_row['tags'].values[0] if not tag_row.empty else "No tags available"

            # Save tags for download
            download_data.append(f"{title}:\n{tags_text}\n\n")

            # Show movie card with tags
            st.markdown(f"""
            <div class="movie-card">
                <img src="{poster}" class="movie-poster" onerror="this.src='https://via.placeholder.com/500x750?text=Poster+Not+Available'">
                <div class="movie-title">{title}</div>
                <div style='color: #bbb; font-size: 12px; text-align: center; margin-top: 8px;'>Tags: {tags_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # Close the grid
        st.markdown('</div>', unsafe_allow_html=True)

        # Add a download button for tags of recommended movies
        buffer = io.StringIO()
        buffer.write("".join(download_data))
        buffer.seek(0)


    else:
        st.subheader(f"Recommended Bollywood Movies Similar to '{selected_movie}':")
        for i, movie in enumerate(recommendations[:10], 1):
            st.write(f"{i}. {movie['title']}")
