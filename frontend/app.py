import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# FastAPI backend URL
API_URL = os.getenv("API_URL", "http://backend:8000")

def main():
    st.set_page_config(page_title="FIFA Rivalry Tracker", layout="wide")
    st.title("FIFA Rivalry Tracker")

    # Navigation
    page = st.sidebar.radio("Navigate", ["Register Player", "Record Match", "Overall Stats", "Head-to-Head Stats", "Match History"])

    if page == "Register Player":
        register_player_page()
    elif page == "Record Match":
        record_match_page()
    elif page == "Overall Stats":
        overall_stats_page()
    elif page == "Head-to-Head Stats":
        head_to_head_stats_page()
    elif page == "Match History":
        match_history_page()

def register_player_page():
    st.header("Register New Player")
    player_name = st.text_input("Player Name")
    if st.button("Register"):
        response = requests.post(f"{API_URL}/players", json={"name": player_name})
        if response.status_code == 200:
            st.success(f"Player {player_name} registered successfully!")
        elif response.status_code == 400:
            st.error("A player with this name already exists. Please choose a unique name.")
        else:
            st.error("Failed to register player. Please try again.")

def record_match_page():
    st.header("Record Match")
    players = get_players()
    player1 = st.selectbox("Player 1", options=players, format_func=lambda x: x['name'], key="record_p1")
    player2 = st.selectbox("Player 2", options=players, format_func=lambda x: x['name'], key="record_p2")
    player1_goals = st.number_input("Player 1 Goals", min_value=0, step=1)
    player2_goals = st.number_input("Player 2 Goals", min_value=0, step=1)
    if st.button("Record Match"):
        if player1['id'] == player2['id']:
            st.error("Players must be different. Please select two different players.")
        else:
            response = requests.post(f"{API_URL}/matches", json={
                "player1_id": player1['id'],
                "player2_id": player2['id'],
                "player1_goals": player1_goals,
                "player2_goals": player2_goals
            })
            if response.status_code == 200:
                st.success("Match recorded successfully!")
            else:
                st.error("Failed to record match. Please try again.")

def overall_stats_page():
    st.header("Overall Player Stats")
    stats = get_stats()
    if stats:
        df = pd.DataFrame(stats)
        goal_difference = df['total_goals_scored'] - df['total_goals_conceded']
        df['goal_difference'] = goal_difference
        df = df.drop(columns=['id'])  # Remove the 'id' column
        df = df.sort_values('points', ascending=False)
        st.dataframe(df)
    else:
        st.warning("No stats available.")

def head_to_head_stats_page():
    st.header("Head-to-Head Stats")
    players = get_players()
    player1 = st.selectbox("Player 1", options=players, format_func=lambda x: x['name'], key="h2h_p1")
    player2 = st.selectbox("Player 2", options=players, format_func=lambda x: x['name'], key="h2h_p2")
    if st.button("Get Head-to-Head Stats"):
        if player1['id'] == player2['id']:
            st.error("Please select two different players.")
        else:
            stats = get_head_to_head_stats(player1['id'], player2['id'])
            if stats:
                st.subheader(f"{stats['player1_name']} vs {stats['player2_name']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Matches", stats['total_matches'])
                col2.metric(f"{stats['player1_name']} Wins", stats['player1_wins'])
                col3.metric(f"{stats['player2_name']} Wins", stats['player2_wins'])
                col1.metric("Draws", stats['draws'])
                col2.metric(f"{stats['player1_name']} Goals", stats['player1_goals'])
                col3.metric(f"{stats['player2_name']} Goals", stats['player2_goals'])
            else:
                st.warning("No head-to-head stats available for these players.")

def match_history_page():
    st.header("Match History")
    matches = get_matches()
    if matches:
        df = pd.DataFrame(matches)
        df = df.drop(columns=['id'])  # Remove the 'id' column
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')  # Format the date
        df = df.sort_values('date', ascending=False)
        st.dataframe(df)
    else:
        st.warning("No matches recorded yet.")

def get_players():
    response = requests.get(f"{API_URL}/players")
    return response.json() if response.status_code == 200 else []

def get_stats():
    response = requests.get(f"{API_URL}/stats")
    return response.json() if response.status_code == 200 else []

def get_matches():
    response = requests.get(f"{API_URL}/matches")
    return response.json() if response.status_code == 200 else []

def get_head_to_head_stats(player1_id, player2_id):
    response = requests.get(f"{API_URL}/head-to-head/{player1_id}/{player2_id}")
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    main()