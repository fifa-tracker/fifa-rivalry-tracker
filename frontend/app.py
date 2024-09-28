import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# FastAPI backend URL
API_URL = os.getenv("API_URL", "http://backend:8000")


def main():
    st.set_page_config(page_title="FIFA Rivalry Tracker", layout="wide")
    st.title("FIFA Rivalry Tracker")

    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        [
            "Record Match",
            "Overall Stats",
            "Head-to-Head Stats",
            "Individual Player Stats",
            "Match History",
            "Edit Match History",
            "Register Player",
        ],
    )

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
    elif page == "Edit Match History":
        edit_match_history_page()
    elif page == "Individual Player Stats":
        individual_player_stats_page()


def register_player_page():
    st.header("Register New Player")
    player_name = st.text_input("Player Name")
    if st.button("Register"):
        response = requests.post(f"{API_URL}/players", json={"name": player_name})
        if response.status_code == 200:
            st.success(f"Player {player_name} registered successfully!")
        elif response.status_code == 400:
            st.error(
                "A player with this name already exists. Please choose a unique name."
            )
        else:
            st.error("Failed to register player. Please try again.")


def record_match_page():
    st.header("Record Match")
    players = get_players()
    player1 = st.selectbox(
        "Player 1", options=players, format_func=lambda x: x["name"], key="record_p1"
    )
    player2 = st.selectbox(
        "Player 2", options=[p for p in players if p != player1], format_func=lambda x: x["name"], key="record_p2"
    )
    player1_goals = st.number_input("Player 1 Goals", min_value=0, step=1)
    player2_goals = st.number_input("Player 2 Goals", min_value=0, step=1)
    if st.button("Record Match"):
        if player1["id"] == player2["id"]:
            st.error("Players must be different. Please select two different players.")
        else:
            response = requests.post(
                f"{API_URL}/matches",
                json={
                    "player1_id": player1["id"],
                    "player2_id": player2["id"],
                    "player1_goals": player1_goals,
                    "player2_goals": player2_goals,
                },
            )
            if response.status_code == 200:
                st.success("Match recorded successfully!")
            else:
                st.error("Failed to record match. Please try again.")


def overall_stats_page():
    st.header("Overall Player Stats")
    stats = get_stats()
    if stats:
        df = pd.DataFrame(stats)
        df = df.drop(columns=['id'])  # Remove the 'id' column
        st.dataframe(df)
    else:
        st.warning("No stats available.")


def head_to_head_stats_page():
    st.header("Head-to-Head Stats")
    players = get_players()
    player1 = st.selectbox(
        "Player 1", options=players, format_func=lambda x: x["name"], key="h2h_p1"
    )
    player2 = st.selectbox(
        "Player 2", options=players, format_func=lambda x: x["name"], key="h2h_p2"
    )
    if st.button("Get Head-to-Head Stats"):
        if player1["id"] == player2["id"]:
            st.error("Please select two different players.")
        else:
            stats = get_head_to_head_stats(player1["id"], player2["id"])
            if stats:
                st.subheader(f"{stats['player1_name']} vs {stats['player2_name']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Matches", stats["total_matches"])
                col2.metric(f"{stats['player1_name']} Wins", stats["player1_wins"])
                col3.metric(f"{stats['player2_name']} Wins", stats["player2_wins"])
                col1.metric("Draws", stats["draws"])
                col2.metric(f"{stats['player1_name']} Goals", stats["player1_goals"])
                col3.metric(f"{stats['player2_name']} Goals", stats["player2_goals"])
            else:
                st.warning("No head-to-head stats available for these players.")


def match_history_page():
    st.header("Match History")
    matches = get_matches()
    if matches:
        df = pd.DataFrame(matches)
        df = df.drop(columns=["id"])  # Remove the 'id' column
        df["date"] = pd.to_datetime(df["date"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )  # Format the date
        df = df.sort_values("date", ascending=False)
        st.dataframe(df)
    else:
        st.warning("No matches recorded yet.")


def individual_player_stats_page():
    st.header("Individual Player Stats")
    players = get_players()
    selected_player = st.selectbox(
        "Select Player", options=players, format_func=lambda x: x["name"]
    )

    if st.button("Get Player Stats"):
        stats = get_player_stats(selected_player["id"])
        if stats:
            st.subheader(f"Stats for {stats['name']}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Matches", stats["total_matches"])
            col2.metric("Wins", stats["wins"])
            col3.metric("Losses", stats["losses"])

            col1.metric("Draws", stats["draws"])
            col2.metric("Points", stats["points"])
            col3.metric("Win Rate", f"{stats['win_rate']:.2%}")

            col1.metric("Total Goals Scored", stats["total_goals_scored"])
            col2.metric("Total Goals Conceded", stats["total_goals_conceded"])
            col3.metric(
                "Goal Difference",
                stats["total_goals_scored"] - stats["total_goals_conceded"],
            )

            col1.metric("Avg. Goals Scored", f"{stats['average_goals_scored']:.2f}")
            col2.metric("Avg. Goals Conceded", f"{stats['average_goals_conceded']:.2f}")

            if stats["highest_wins_against"]:
                opponent, wins = list(stats["highest_wins_against"].items())[0]
                st.info(f"Most wins against: {opponent} ({wins} wins)")

            if stats["highest_losses_against"]:
                opponent, losses = list(stats["highest_losses_against"].items())[0]
                st.info(f"Most losses against: {opponent} ({losses} losses)")

            # Daily Winrate graph
            st.subheader("Daily Winrate Over Time")
            fig = go.Figure()
            dates = [
                datetime.fromisoformat(item["date"])
                for item in stats["winrate_over_time"]
            ]
            winrates = [item["winrate"] for item in stats["winrate_over_time"]]
            fig.add_trace(
                go.Scatter(
                    x=dates, y=winrates, mode="lines+markers", name="Daily Winrate"
                )
            )
            fig.update_layout(
                title="Daily Winrate Over Time",
                xaxis_title="Date",
                yaxis_title="Winrate",
                yaxis_tickformat=".0%",
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No stats available for this player.")


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


def get_player_stats(player_id):
    response = requests.get(f"{API_URL}/player/{player_id}/stats")
    return response.json() if response.status_code == 200 else None


def edit_match_history_page():
    st.header("Edit Match History")

    matches = get_matches()
    if not matches:
        st.warning("No matches found.")
        return

    selected_match = st.selectbox(
        "Select a match to edit",
        options=matches,
        format_func=lambda x: f"{x['player1_name']} vs {x['player2_name']} ({x['player1_goals']}-{x['player2_goals']}) on {x['date']}",
    )

    if selected_match:
        st.subheader(
            f"Editing match: {selected_match['player1_name']} vs {selected_match['player2_name']}"
        )

        col1, col2 = st.columns(2)
        with col1:
            player1_goals = st.number_input(
                f"{selected_match['player1_name']} Goals",
                min_value=0,
                value=selected_match["player1_goals"],
            )
        with col2:
            player2_goals = st.number_input(
                f"{selected_match['player2_name']} Goals",
                min_value=0,
                value=selected_match["player2_goals"],
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Match"):
                updated_match = update_match(
                    selected_match["id"], player1_goals, player2_goals
                )
                if updated_match:
                    st.success("Match updated successfully!")
                else:
                    st.error("Failed to update match. Please try again.")

        with col2:
            delete_confirmation = st.checkbox(
                "I confirm that I want to delete this match"
            )
            if st.button(
                "Delete Match", type="secondary", disabled=not delete_confirmation
            ):
                if delete_match(selected_match["id"]):
                    st.success("Match deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete match. Please try again.")


def update_match(match_id, player1_goals, player2_goals):
    response = requests.put(
        f"{API_URL}/matches/{match_id}",
        json={"player1_goals": player1_goals, "player2_goals": player2_goals},
    )
    return response.json() if response.status_code == 200 else None


def delete_match(match_id):
    response = requests.delete(f"{API_URL}/matches/{match_id}")
    return response.status_code == 200


if __name__ == "__main__":
    main()
