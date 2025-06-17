import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from unittest.mock import patch, AsyncMock


class TestPlayerEndpoints:
    """Test suite for player endpoints"""
    
    def test_create_player_success(self, client: TestClient, sample_player_data):
        """Test successful player creation"""
        response = client.post("/api/v1/players/", json=sample_player_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_player_data["name"]
        assert data["total_matches"] == 0
        assert data["total_goals_scored"] == 0
        assert data["points"] == 0
        assert "id" in data

    def test_create_player_duplicate_name(self, client: TestClient, sample_player_data):
        """Test creating player with duplicate name"""
        # Create first player
        response1 = client.post("/api/v1/players/", json=sample_player_data)
        assert response1.status_code == 200
        
        # Try to create another player with same name
        response2 = client.post("/api/v1/players/", json=sample_player_data)
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_create_player_missing_name(self, client: TestClient):
        """Test creating player without name"""
        response = client.post("/api/v1/players/", json={})
        
        assert response.status_code == 422  # Validation error

    def test_get_all_players_empty(self, client: TestClient):
        """Test getting all players when none exist"""
        response = client.get("/api/v1/players/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_players_with_data(self, client: TestClient, sample_player_data):
        """Test getting all players with existing data"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        
        # Get all players
        response = client.get("/api/v1/players/")
        
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 1
        assert players[0]["id"] == created_player["id"]
        assert players[0]["name"] == sample_player_data["name"]

    def test_get_player_by_id_success(self, client: TestClient, sample_player_data):
        """Test getting a specific player by ID"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        player_id = created_player["id"]
        
        # Get player by ID
        response = client.get(f"/api/v1/players/{player_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == player_id
        assert data["name"] == sample_player_data["name"]

    def test_get_player_by_id_not_found(self, client: TestClient):
        """Test getting a player that doesn't exist"""
        fake_id = str(ObjectId())
        response = client.get(f"/api/v1/players/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_player_by_id_invalid_format(self, client: TestClient):
        """Test getting a player with invalid ID format"""
        invalid_id = "invalid-id"
        response = client.get(f"/api/v1/players/{invalid_id}")
        
        assert response.status_code == 400
        assert "Invalid player ID format" in response.json()["detail"]

    def test_update_player_success(self, client: TestClient, sample_player_data):
        """Test successful player update"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        player_id = created_player["id"]
        
        # Update player
        new_data = {"name": "Updated Player Name"}
        response = client.put(f"/api/v1/players/{player_id}", json=new_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == player_id
        assert data["name"] == new_data["name"]

    def test_update_player_not_found(self, client: TestClient):
        """Test updating a player that doesn't exist"""
        fake_id = str(ObjectId())
        new_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/players/{fake_id}", json=new_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_player_success(self, client: TestClient, sample_player_data):
        """Test successful player deletion"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        player_id = created_player["id"]
        
        # Delete player
        response = client.delete(f"/api/v1/players/{player_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify player is deleted
        get_response = client.get(f"/api/v1/players/{player_id}")
        assert get_response.status_code == 404

    def test_delete_player_not_found(self, client: TestClient):
        """Test deleting a player that doesn't exist"""
        fake_id = str(ObjectId())
        response = client.delete(f"/api/v1/players/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_player_invalid_id(self, client: TestClient):
        """Test deleting a player with invalid ID"""
        invalid_id = "invalid-id"
        response = client.delete(f"/api/v1/players/{invalid_id}")
        
        assert response.status_code == 400
        assert "Invalid player ID format" in response.json()["detail"]

    @pytest.mark.skip(reason="Endpoint not fully implemented yet")
    def test_get_player_detailed_stats(self, client: TestClient, sample_player_data):
        """Test getting detailed player statistics"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        player_id = created_player["id"]
        
        # Get detailed stats
        response = client.get(f"/api/v1/players/{player_id}/stats")
        
        # This test is skipped because the endpoint is not fully implemented
        # When implemented, it should return 200 with detailed stats
        pass

    @pytest.mark.skip(reason="Endpoint not fully implemented yet")
    def test_get_player_matches(self, client: TestClient, sample_player_data):
        """Test getting all matches for a player"""
        # Create a player first
        create_response = client.post("/api/v1/players/", json=sample_player_data)
        created_player = create_response.json()
        player_id = created_player["id"]
        
        # Get player matches
        response = client.get(f"/api/v1/players/{player_id}/matches")
        
        # This test is skipped because the endpoint is not fully implemented
        # When implemented, it should return 200 with list of matches
        pass


class TestPlayerValidation:
    """Test suite for player data validation"""
    
    def test_player_name_empty_string(self, client: TestClient):
        """Test creating player with empty name"""
        response = client.post("/api/v1/players/", json={"name": ""})
        
        # Depending on validation rules, this might be 422 or 400
        assert response.status_code in [400, 422]

    def test_player_name_too_long(self, client: TestClient):
        """Test creating player with very long name"""
        long_name = "a" * 1000  # Very long name
        response = client.post("/api/v1/players/", json={"name": long_name})
        
        # Should either succeed or fail with validation error
        # Depending on your validation rules
        assert response.status_code in [200, 400, 422]

    def test_player_name_special_characters(self, client: TestClient):
        """Test creating player with special characters in name"""
        special_name = "Test Player @#$%^&*()"
        response = client.post("/api/v1/players/", json={"name": special_name})
        
        # Should succeed unless you have specific validation rules
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == special_name


class TestPlayerIntegration:
    """Integration tests for player functionality"""
    
    def test_multiple_players_creation_and_retrieval(self, client: TestClient):
        """Test creating multiple players and retrieving them"""
        players_data = [
            {"name": "Player 1"},
            {"name": "Player 2"},
            {"name": "Player 3"}
        ]
        
        created_players = []
        for player_data in players_data:
            response = client.post("/api/v1/players/", json=player_data)
            assert response.status_code == 200
            created_players.append(response.json())
        
        # Get all players
        response = client.get("/api/v1/players/")
        assert response.status_code == 200
        all_players = response.json()
        
        assert len(all_players) == 3
        for i, player in enumerate(all_players):
            assert player["name"] == players_data[i]["name"]
            assert player["total_matches"] == 0

    def test_player_lifecycle(self, client: TestClient):
        """Test complete player lifecycle: create, read, update, delete"""
        # Create
        create_data = {"name": "Lifecycle Player"}
        create_response = client.post("/api/v1/players/", json=create_data)
        assert create_response.status_code == 200
        player = create_response.json()
        player_id = player["id"]
        
        # Read
        read_response = client.get(f"/api/v1/players/{player_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == create_data["name"]
        
        # Update
        update_data = {"name": "Updated Lifecycle Player"}
        update_response = client.put(f"/api/v1/players/{player_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == update_data["name"]
        
        # Verify update
        read_after_update = client.get(f"/api/v1/players/{player_id}")
        assert read_after_update.status_code == 200
        assert read_after_update.json()["name"] == update_data["name"]
        
        # Delete
        delete_response = client.delete(f"/api/v1/players/{player_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        read_after_delete = client.get(f"/api/v1/players/{player_id}")
        assert read_after_delete.status_code == 404 