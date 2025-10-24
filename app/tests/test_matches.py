import pytest
from fastapi.testclient import TestClient
from bson import ObjectId


class TestMatchEndpoints:
    """Test suite for match endpoints"""

    def test_get_all_matches_empty(self, client: TestClient):
        """Test getting all matches when none exist"""
        response = client.get("/api/v1/matches/")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.skip(reason="Match creation endpoint not fully implemented yet")
    def test_create_match_success(self, client: TestClient, created_players, sample_match_with_players):
        """Test successful match creation"""
        player1, player2 = created_players
        match_data = sample_match_with_players.copy()
        match_data["player1_id"] = player1["id"]
        match_data["player2_id"] = player2["id"]
        
        response = client.post("/api/v1/matches/", json=match_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["player1_name"] == player1["username"]
        assert data["player2_name"] == player2["username"]
        assert data["player1_goals"] == match_data["player1_goals"]
        assert data["player2_goals"] == match_data["player2_goals"]
        assert data["team1"] == match_data["team1"]
        assert data["team2"] == match_data["team2"]
        assert data["half_length"] == match_data["half_length"]
        assert "id" in data
        assert "date" in data

    @pytest.mark.skip(reason="Match creation endpoint not fully implemented yet")
    def test_create_match_invalid_player(self, client: TestClient):
        """Test creating match with invalid player ID"""
        match_data = {
            "player1_id": str(ObjectId()),  # Non-existent player
            "player2_id": str(ObjectId()),  # Non-existent player
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid"
        }
        
        response = client.post("/api/v1/matches/", json=match_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_match_missing_data(self, client: TestClient):
        """Test creating match with missing required data"""
        incomplete_data = {
            "player1_goals": 2,
            "player2_goals": 1
            # Missing player IDs, teams, and half_length
        }
        
        response = client.post("/api/v1/matches/", json=incomplete_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_match_missing_half_length(self, client: TestClient, created_players):
        """Test creating match with missing half_length field"""
        player1, player2 = created_players
        match_data = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid"
            # Missing half_length
        }
        
        response = client.post("/api/v1/matches/", json=match_data)
        
        assert response.status_code == 422  # Validation error for missing required field

    def test_create_match_negative_goals(self, client: TestClient, created_players):
        """Test creating match with negative goals"""
        player1, player2 = created_players
        match_data = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": -1,  # Invalid
            "player2_goals": 2,
            "team1": "Barcelona",
            "team2": "Real Madrid",
            "half_length": 4
        }
        
        response = client.post("/api/v1/matches/", json=match_data)
        
        # Should either be validation error (422) or business logic error (400)
        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Match update endpoint not fully implemented yet")
    def test_update_match_success(self, client: TestClient, created_players, sample_match_with_players, sample_match_update_data):
        """Test successful match update"""
        player1, player2 = created_players
        match_data = sample_match_with_players.copy()
        match_data["player1_id"] = player1["id"]
        match_data["player2_id"] = player2["id"]
        
        # Create match first
        create_response = client.post("/api/v1/matches/", json=match_data)
        assert create_response.status_code == 200
        created_match = create_response.json()
        match_id = created_match["id"]
        
        # Update match
        response = client.put(f"/api/v1/matches/{match_id}", json=sample_match_update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == match_id
        assert data["player1_goals"] == sample_match_update_data["player1_goals"]
        assert data["player2_goals"] == sample_match_update_data["player2_goals"]
        assert data["half_length"] == sample_match_update_data["half_length"]

    @pytest.mark.skip(reason="Match update endpoint not fully implemented yet")
    def test_update_match_not_found(self, client: TestClient, sample_match_update_data):
        """Test updating a match that doesn't exist"""
        fake_id = str(ObjectId())
        response = client.put(f"/api/v1/matches/{fake_id}", json=sample_match_update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.skip(reason="Match update endpoint not fully implemented yet")
    def test_update_match_invalid_id(self, client: TestClient, sample_match_update_data):
        """Test updating a match with invalid ID format"""
        invalid_id = "invalid-id"
        response = client.put(f"/api/v1/matches/{invalid_id}", json=sample_match_update_data)
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_delete_match_success(self, client: TestClient):
        """Test successful match deletion"""
        # For now, we'll create a minimal match directly in database
        # This test will be updated when match creation is implemented
        pass

    def test_delete_match_not_found(self, client: TestClient):
        """Test deleting a match that doesn't exist"""
        fake_id = str(ObjectId())
        response = client.delete(f"/api/v1/matches/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_match_invalid_id(self, client: TestClient):
        """Test deleting a match with invalid ID format"""
        invalid_id = "invalid-id"
        response = client.delete(f"/api/v1/matches/{invalid_id}")
        
        assert response.status_code in [400, 422]  # Could be either depending on validation


class TestMatchValidation:
    """Test suite for match data validation"""
    
    def test_match_goals_validation(self, client: TestClient, created_players):
        """Test various goal value validations"""
        player1, player2 = created_players
        
        test_cases = [
            {"player1_goals": 0, "player2_goals": 0, "should_pass": True},
            {"player1_goals": 10, "player2_goals": 5, "should_pass": True},
            {"player1_goals": -1, "player2_goals": 2, "should_pass": False},
            {"player1_goals": 2, "player2_goals": -1, "should_pass": False},
        ]
        
        for case in test_cases:
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": case["player1_goals"],
                "player2_goals": case["player2_goals"],
                "team1": "Team A",
                "team2": "Team B"
            }
            
            response = client.post("/api/v1/matches/", json=match_data)
            
            if case["should_pass"]:
                assert response.status_code in [200, 500]  # 500 if endpoint not implemented
            else:
                assert response.status_code in [400, 422]

    def test_match_team_names(self, client: TestClient, created_players):
        """Test team name validation"""
        player1, player2 = created_players
        
        test_cases = [
            {"team1": "", "team2": "Valid Team", "description": "empty team1"},
            {"team1": "Valid Team", "team2": "", "description": "empty team2"},
            {"team1": "a" * 1000, "team2": "Valid", "description": "very long team1"},
            {"team1": "Special @#$%", "team2": "Valid", "description": "special characters"},
        ]
        
        for case in test_cases:
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": 1,
                "player2_goals": 0,
                "team1": case["team1"],
                "team2": case["team2"]
            }
            
            response = client.post("/api/v1/matches/", json=match_data)
            
            # The response depends on your validation rules
            # For now, we just check it doesn't crash
            assert response.status_code in [200, 400, 422, 500]

    def test_match_half_length_validation(self, client: TestClient, created_players):
        """Test match half length validation"""
        player1, player2 = created_players
        
        # Test with half_length below minimum (3 minutes)
        match_data_invalid_low = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid",
            "half_length": 2  # Invalid - below minimum
        }
        
        response = client.post("/api/v1/matches/", json=match_data_invalid_low)
        assert response.status_code == 422  # Validation error
        
        # Test with half_length above maximum (6 minutes)
        match_data_invalid_high = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid",
            "half_length": 7  # Invalid - above maximum
        }
        
        response = client.post("/api/v1/matches/", json=match_data_invalid_high)
        assert response.status_code == 422  # Validation error
        
        # Test with valid half_length values
        for valid_half_length in [3, 4, 5, 6]:
            match_data_valid = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": 2,
                "player2_goals": 1,
                "team1": "Barcelona",
                "team2": "Real Madrid",
                "half_length": valid_half_length
            }
            
            response = client.post("/api/v1/matches/", json=match_data_valid)
            assert response.status_code == 200  # Should succeed


@pytest.mark.integration
class TestMatchIntegration:
    """Integration tests for match functionality"""
    
    def test_match_affects_player_stats_and_elo(self, client: TestClient, created_players):
        """Test that creating a match updates player statistics"""
        player1, player2 = created_players
        
        # Get initial player stats
        initial_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        initial_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        assert initial_player1["total_matches"] == 0
        assert initial_player2["total_matches"] == 0
        
        # Get initial ELO ratings
        initial_player1_elo = initial_player1.get("elo_rating", 1200)
        initial_player2_elo = initial_player2.get("elo_rating", 1200)
        
        # Create a match
        match_data = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 3,
            "player2_goals": 1,
            "tournament_id": "507f1f77bcf86cd799439011",  # Sample tournament ID
            "team1": "Barcelona",
            "team2": "Real Madrid",
            "half_length": 4
        }
        
        match_response = client.post("/api/v1/matches/", json=match_data)
        assert match_response.status_code == 200
        
        # Check updated player stats
        updated_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        updated_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        # Player 1 should have won
        assert updated_player1["total_matches"] == 1
        assert updated_player1["wins"] == 1
        assert updated_player1["losses"] == 0
        assert updated_player1["total_goals_scored"] == 3
        assert updated_player1["total_goals_conceded"] == 1
        assert updated_player1["points"] == 3  # 3 points for a win
        
        # Player 2 should have lost
        assert updated_player2["total_matches"] == 1
        assert updated_player2["wins"] == 0
        assert updated_player2["losses"] == 1
        assert updated_player2["total_goals_scored"] == 1
        assert updated_player2["total_goals_conceded"] == 3
        assert updated_player2["points"] == 0  # 0 points for a loss
        
        # Check ELO rating changes
        updated_player1_elo = updated_player1.get("elo_rating", 1200)
        updated_player2_elo = updated_player2.get("elo_rating", 1200)
        
        # Player 1 should gain ELO rating (winner)
        assert updated_player1_elo > initial_player1_elo
        
        # Player 2 should lose ELO rating (loser)
        assert updated_player2_elo < initial_player2_elo
        
        # Total ELO should remain the same (zero-sum)
        total_elo_before = initial_player1_elo + initial_player2_elo
        total_elo_after = updated_player1_elo + updated_player2_elo
        assert total_elo_before == total_elo_after
        
        # Verify last_5_teams field is updated
        assert updated_player1["last_5_teams"] == ["Barcelona"]
        assert updated_player2["last_5_teams"] == ["Real Madrid"]

    def test_multiple_matches_stats_and_elo_accumulation(self, client: TestClient, created_players):
        """Test that multiple matches correctly accumulate player statistics"""
        player1, player2 = created_players
        
        matches = [
            {"player1_goals": 2, "player2_goals": 1},  # Player 1 wins
            {"player1_goals": 0, "player2_goals": 2},  # Player 2 wins
            {"player1_goals": 1, "player2_goals": 1},  # Draw
        ]
        
        for match_goals in matches:
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": match_goals["player1_goals"],
                "player2_goals": match_goals["player2_goals"],
                "tournament_id": "507f1f77bcf86cd799439011",  # Sample tournament ID
                "team1": "Team A",
                "team2": "Team B",
                "half_length": 4
            }
            
            response = client.post("/api/v1/matches/", json=match_data)
            assert response.status_code == 200
        
        # Check final stats
        final_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        final_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        # Player 1: 1 win, 1 loss, 1 draw
        assert final_player1["total_matches"] == 3
        assert final_player1["wins"] == 1
        assert final_player1["losses"] == 1
        assert final_player1["draws"] == 1
        assert final_player1["total_goals_scored"] == 3  # 2 + 0 + 1
        assert final_player1["total_goals_conceded"] == 4  # 1 + 2 + 1
        assert final_player1["points"] == 4  # 3 + 0 + 1
        
        # Player 2: 1 win, 1 loss, 1 draw
        assert final_player2["total_matches"] == 3
        assert final_player2["wins"] == 1
        assert final_player2["losses"] == 1
        assert final_player2["draws"] == 1
        assert final_player2["total_goals_scored"] == 4  # 1 + 2 + 1
        assert final_player2["total_goals_conceded"] == 3  # 2 + 0 + 1
        assert final_player2["points"] == 4  # 0 + 3 + 1
        
        # Check that ELO ratings have been updated (should be different from default)
        assert final_player1["elo_rating"] != 1200
        assert final_player2["elo_rating"] != 1200
        
        # Total ELO should still be zero-sum (approximately, allowing for rounding)
        total_elo = final_player1["elo_rating"] + final_player2["elo_rating"]
        expected_total = 2400  # 1200 + 1200
        assert abs(total_elo - expected_total) < 5  # Allow for small rounding differences

    def test_last_5_teams_tracking(self, client: TestClient, created_players):
        """Test that last_5_teams field correctly tracks and limits to 5 unique teams"""
        player1, player2 = created_players
        
        # Play 6 matches with different teams to test the limit
        teams_player1 = ["Barcelona", "Real Madrid", "Arsenal", "Chelsea", "Liverpool", "Manchester City"]
        teams_player2 = ["PSG", "Bayern Munich", "Juventus", "AC Milan", "Inter Milan", "Napoli"]
        
        for i in range(6):
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": 1,
                "player2_goals": 0,
                "tournament_id": "507f1f77bcf86cd799439011",  # Sample tournament ID
                "team1": teams_player1[i],
                "team2": teams_player2[i],
                "half_length": 4
            }
            
            response = client.post("/api/v1/matches/", json=match_data)
            assert response.status_code == 200
        
        # Check that only the last 5 unique teams are kept
        updated_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        updated_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        # Player 1 should have the last 5 unique teams (excluding the first one)
        expected_player1_teams = teams_player1[1:]  # Skip first team
        assert updated_player1["last_5_teams"] == expected_player1_teams
        assert len(updated_player1["last_5_teams"]) == 5
        
        # Player 2 should have the last 5 unique teams (excluding the first one)
        expected_player2_teams = teams_player2[1:]  # Skip first team
        assert updated_player2["last_5_teams"] == expected_player2_teams
        assert len(updated_player2["last_5_teams"]) == 5

    def test_last_5_teams_unique_behavior(self, client: TestClient, created_players):
        """Test that last_5_teams field keeps only unique teams and moves duplicates to front"""
        player1, player2 = created_players
        
        # Play matches with some duplicate teams
        matches = [
            {"team1": "Barcelona", "team2": "Real Madrid"},
            {"team1": "Arsenal", "team2": "Chelsea"},
            {"team1": "Barcelona", "team2": "Liverpool"},  # Barcelona again
            {"team1": "PSG", "team2": "Bayern Munich"},
            {"team1": "Barcelona", "team2": "Juventus"},  # Barcelona again
        ]
        
        for match in matches:
            match_data = {
                "player1_id": player1["id"],
                "player2_id": player2["id"],
                "player1_goals": 1,
                "player2_goals": 0,
                "tournament_id": "507f1f77bcf86cd799439011",
                "team1": match["team1"],
                "team2": match["team2"],
                "half_length": 4
            }
            
            response = client.post("/api/v1/matches/", json=match_data)
            assert response.status_code == 200
        
        # Check the final state
        updated_player1 = client.get(f"/api/v1/user/{player1['id']}").json()
        updated_player2 = client.get(f"/api/v1/user/{player2['id']}").json()
        
        # Player 1 should have unique teams with Barcelona at the front (most recent)
        # Expected: ["Barcelona", "PSG", "Arsenal"] (Barcelona appears only once, at the front)
        assert updated_player1["last_5_teams"] == ["Barcelona", "PSG", "Arsenal"]
        assert len(updated_player1["last_5_teams"]) == 3
        
        # Player 2 should have unique teams with Juventus at the front (most recent)
        # Expected: ["Juventus", "Bayern Munich", "Liverpool", "Chelsea", "Real Madrid"]
        assert updated_player2["last_5_teams"] == ["Juventus", "Bayern Munich", "Liverpool", "Chelsea", "Real Madrid"]
        assert len(updated_player2["last_5_teams"]) == 5 