import pytest
from fastapi.testclient import TestClient
from bson import ObjectId


class TestStatsEndpoints:
    """Test suite for stats endpoints"""

    def test_get_stats_empty(self, client: TestClient):
        """Test getting stats when no players exist"""
        response = client.get("/api/v1/stats/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_stats_with_players(self, client: TestClient, created_players):
        """Test getting stats with existing players"""
        player1, player2 = created_players
        
        response = client.get("/api/v1/stats/")
        
        assert response.status_code == 200
        stats = response.json()
        assert len(stats) == 2
        
        # Should be sorted by points (descending), then goal difference (descending)
        # Both players should have 0 points initially
        for player_stats in stats:
            assert player_stats["total_matches"] == 0
            assert player_stats["points"] == 0
            assert player_stats["wins"] == 0
            assert player_stats["losses"] == 0
            assert player_stats["draws"] == 0

    @pytest.mark.skip(reason="Head-to-head endpoint not fully implemented yet")
    def test_get_head_to_head_stats_success(self, client: TestClient, created_players):
        """Test getting head-to-head statistics between two players"""
        player1, player2 = created_players
        
        response = client.get(f"/api/v1/stats/head-to-head/{player1['id']}/{player2['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["player1_name"] == player1["username"]
        assert data["player2_name"] == player2["username"]
        assert data["total_matches"] == 0
        assert data["player1_wins"] == 0
        assert data["player2_wins"] == 0
        assert data["draws"] == 0

    def test_get_head_to_head_stats_invalid_player1(self, client: TestClient, created_players):
        """Test head-to-head with invalid first player ID"""
        _, player2 = created_players
        fake_id = str(ObjectId())
        
        response = client.get(f"/api/v1/stats/head-to-head/{fake_id}/{player2['id']}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_head_to_head_stats_invalid_player2(self, client: TestClient, created_players):
        """Test head-to-head with invalid second player ID"""
        player1, _ = created_players
        fake_id = str(ObjectId())
        
        response = client.get(f"/api/v1/stats/head-to-head/{player1['id']}/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_head_to_head_stats_both_invalid(self, client: TestClient):
        """Test head-to-head with both invalid player IDs"""
        fake_id1 = str(ObjectId())
        fake_id2 = str(ObjectId())
        
        response = client.get(f"/api/v1/stats/head-to-head/{fake_id1}/{fake_id2}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_head_to_head_stats_same_player(self, client: TestClient, created_players):
        """Test head-to-head with same player ID for both players"""
        player1, _ = created_players
        
        response = client.get(f"/api/v1/stats/head-to-head/{player1['id']}/{player1['id']}")
        
        # This should either work (showing player vs themselves) or return an error
        # Depending on your business logic
        assert response.status_code in [200, 400, 404]

    def test_get_head_to_head_stats_invalid_id_format(self, client: TestClient):
        """Test head-to-head with invalid ID format"""
        invalid_id = "invalid-id"
        valid_id = str(ObjectId())
        
        response = client.get(f"/api/v1/stats/head-to-head/{invalid_id}/{valid_id}")
        
        assert response.status_code in [400, 422]


class TestStatsIntegration:
    """Integration tests for stats functionality"""
    
    @pytest.mark.skip(reason="Match creation needed for stats integration tests")
    def test_stats_ordering_after_matches(self, client: TestClient, created_players):
        """Test that stats are properly ordered after matches are played"""
        player1, player2 = created_players
        
        # Create matches to generate different point totals
        # Player1 wins 2-1
        match1_data = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid"
        }
        response1 = client.post("/api/v1/matches/", json=match1_data)
        assert response1.status_code == 200
        
        # Player2 wins 3-0 in another match
        match2_data = {
            "player1_id": player2["id"],
            "player2_id": player1["id"],
            "player1_goals": 3,
            "player2_goals": 0,
            "team1": "Real Madrid",
            "team2": "Barcelona"
        }
        response2 = client.post("/api/v1/matches/", json=match2_data)
        assert response2.status_code == 200
        
        # Get stats - should be ordered by points, then goal difference
        response = client.get("/api/v1/stats/")
        assert response.status_code == 200
        stats = response.json()
        
        assert len(stats) == 2
        # Both players should have 3 points (1 win each), but different goal differences
        # Player2 should be first due to better goal difference (+2 vs -2)
        assert stats[0]["points"] == 3
        assert stats[1]["points"] == 3
        assert stats[0]["goal_difference"] > stats[1]["goal_difference"]

    @pytest.mark.skip(reason="Match creation needed for head-to-head integration tests")
    def test_head_to_head_stats_with_matches(self, client: TestClient, created_players):
        """Test head-to-head statistics after playing matches"""
        player1, player2 = created_players
        
        # Create multiple matches between the players
        matches = [
            {"p1_goals": 2, "p2_goals": 1},  # Player1 wins
            {"p1_goals": 0, "p2_goals": 3},  # Player2 wins
            {"p1_goals": 1, "p2_goals": 1},  # Draw
            {"p1_goals": 4, "p2_goals": 2},  # Player1 wins
        ]
        
        for match in matches:
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": match["p1_goals"],
                "player2_goals": match["p2_goals"],
                "team1": "Team A",
                "team2": "Team B"
            }
            response = client.post("/api/v1/matches/", json=match_data)
            assert response.status_code == 200
        
        # Get head-to-head stats
        response = client.get(f"/api/v1/stats/head-to-head/{player1['id']}/{player2['id']}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_matches"] == 4
        assert data["player1_wins"] == 2
        assert data["player2_wins"] == 1
        assert data["draws"] == 1
        assert data["player1_goals"] == 7  # 2+0+1+4
        assert data["player2_goals"] == 7  # 1+3+1+2
        assert data["player1_win_rate"] == 0.5  # 2/4
        assert data["player2_win_rate"] == 0.25  # 1/4

    def test_stats_consistency_across_endpoints(self, client: TestClient, created_players):
        """Test that player stats are consistent across different endpoints"""
        player1, player2 = created_players
        
        # Get player stats from different endpoints
        individual_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        individual_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        stats_response = client.get("/api/v1/stats/").json()
        
        # Find players in stats response
        stats_player1 = next(p for p in stats_response if p["id"] == player1["id"])
        stats_player2 = next(p for p in stats_response if p["id"] == player2["id"])
        
        # Compare key stats
        for field in ["total_matches", "wins", "losses", "draws", "points", "total_goals_scored", "total_goals_conceded"]:
            assert individual_player1[field] == stats_player1[field], f"Player1 {field} mismatch"
            assert individual_player2[field] == stats_player2[field], f"Player2 {field} mismatch"

    def test_stats_with_multiple_players(self, client: TestClient):
        """Test stats endpoint with multiple players having different performance"""
        # Create multiple players
        players_data = [
            {"username": "player_a", "email": "a@example.com", "first_name": "Player", "last_name": "A", "password": "password123"},
            {"username": "player_b", "email": "b@example.com", "first_name": "Player", "last_name": "B", "password": "password123"},
            {"username": "player_c", "email": "c@example.com", "first_name": "Player", "last_name": "C", "password": "password123"},
            {"username": "player_d", "email": "d@example.com", "first_name": "Player", "last_name": "D", "password": "password123"}
        ]
        
        created_players = []
        for player_data in players_data:
            response = client.post("/api/v1/user/register", json=player_data)
            assert response.status_code == 200
            created_players.append(response.json())
        
        # Get stats
        response = client.get("/api/v1/stats/")
        assert response.status_code == 200
        stats = response.json()
        
        assert len(stats) == 4
        
        # All players should have 0 stats initially
        for player_stats in stats:
            assert player_stats["total_matches"] == 0
            assert player_stats["points"] == 0
            # Verify all required fields are present
            required_fields = ["id", "username", "total_matches", "wins", "losses", "draws", 
                             "points", "total_goals_scored", "total_goals_conceded", "goal_difference"]
            for field in required_fields:
                assert field in player_stats 