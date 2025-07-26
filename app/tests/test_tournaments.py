import pytest
from fastapi.testclient import TestClient
from bson import ObjectId


class TestTournamentEndpoints:
    """Test suite for tournament endpoints"""

    def test_create_tournament_success(self, client: TestClient, sample_tournament_data):
        """Test successful tournament creation"""
        response = client.post("/api/v1/tournaments/", json=sample_tournament_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_tournament_data["name"]
        assert data["description"] == sample_tournament_data["description"]
        assert "id" in data
        assert "start_date" in data
        assert data["matches_count"] == 0

    def test_create_tournament_minimal_data(self, client: TestClient):
        """Test creating tournament with minimal required data"""
        minimal_data = {"name": "Minimal Tournament"}
        response = client.post("/api/v1/tournaments/", json=minimal_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == minimal_data["name"]
        assert "id" in data
        assert "start_date" in data

    def test_create_tournament_missing_name(self, client: TestClient):
        """Test creating tournament without name"""
        response = client.post("/api/v1/tournaments/", json={})
        
        assert response.status_code == 422  # Validation error

    def test_get_all_tournaments_empty(self, client: TestClient):
        """Test getting all tournaments when none exist"""
        response = client.get("/api/v1/tournaments/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_tournaments_with_data(self, client: TestClient, sample_tournament_data):
        """Test getting all tournaments with existing data"""
        # Create a tournament first
        create_response = client.post("/api/v1/tournaments/", json=sample_tournament_data)
        created_tournament = create_response.json()
        
        # Get all tournaments
        response = client.get("/api/v1/tournaments/")
        
        assert response.status_code == 200
        tournaments = response.json()
        assert len(tournaments) == 1
        assert tournaments[0]["id"] == created_tournament["id"]
        assert tournaments[0]["name"] == sample_tournament_data["name"]

    def test_get_tournament_matches_empty(self, client: TestClient, created_tournament):
        """Test getting tournament matches when tournament has no matches"""
        tournament_id = created_tournament["id"]
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50  # Default page size
        assert data["total_pages"] == 0
        assert data["has_next"] is False
        assert data["has_previous"] is False

    def test_get_tournament_matches_invalid_id(self, client: TestClient):
        """Test getting matches for non-existent tournament"""
        fake_id = str(ObjectId())
        response = client.get(f"/api/v1/tournaments/{fake_id}/matches")
        
        assert response.status_code == 404  # Now returns 404 for non-existent tournament


class TestTournamentValidation:
    """Test suite for tournament data validation"""
    
    def test_tournament_name_empty_string(self, client: TestClient):
        """Test creating tournament with empty name"""
        response = client.post("/api/v1/tournaments/", json={"name": ""})
        
        # Depending on validation rules, this might be 422 or 400
        assert response.status_code in [400, 422]

    def test_tournament_name_too_long(self, client: TestClient):
        """Test creating tournament with very long name"""
        long_name = "a" * 1000  # Very long name
        response = client.post("/api/v1/tournaments/", json={"name": long_name})
        
        # Should either succeed or fail with validation error
        assert response.status_code in [200, 400, 422]

    def test_tournament_name_special_characters(self, client: TestClient):
        """Test creating tournament with special characters in name"""
        special_name = "Tournament @#$%^&*()"
        response = client.post("/api/v1/tournaments/", json={"name": special_name})
        
        # Should succeed unless you have specific validation rules
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == special_name

    def test_tournament_description_validation(self, client: TestClient):
        """Test tournament description validation"""
        test_cases = [
            {"description": None, "should_pass": True},
            {"description": "", "should_pass": True},
            {"description": "Valid description", "should_pass": True},
            {"description": "a" * 5000, "should_pass": True},  # Very long description
        ]
        
        for case in test_cases:
            tournament_data = {"name": "Test Tournament"}
            if case["description"] is not None:
                tournament_data["description"] = case["description"]
            
            response = client.post("/api/v1/tournaments/", json=tournament_data)
            
            if case["should_pass"]:
                assert response.status_code == 200
            else:
                assert response.status_code in [400, 422]


class TestTournamentIntegration:
    """Integration tests for tournament functionality"""
    
    def test_multiple_tournaments_creation(self, client: TestClient):
        """Test creating multiple tournaments"""
        tournaments_data = [
            {"name": "Tournament 1", "description": "First tournament"},
            {"name": "Tournament 2", "description": "Second tournament"},
            {"name": "Tournament 3"},  # No description
        ]
        
        created_tournaments = []
        for tournament_data in tournaments_data:
            response = client.post("/api/v1/tournaments/", json=tournament_data)
            assert response.status_code == 200
            created_tournaments.append(response.json())
        
        # Get all tournaments
        response = client.get("/api/v1/tournaments/")
        assert response.status_code == 200
        all_tournaments = response.json()
        
        assert len(all_tournaments) == 3
        for i, tournament in enumerate(all_tournaments):
            assert tournament["name"] == tournaments_data[i]["name"]

    @pytest.mark.skip(reason="Tournament-match relationship not fully implemented yet")
    def test_tournament_with_matches(self, client: TestClient, created_tournament, created_players):
        """Test tournament with associated matches"""
        tournament_id = created_tournament["id"]
        player1, player2 = created_players
        
        # Create matches associated with tournament
        match_data = {
            "player1_id": player1["id"],
            "player2_id": player2["id"],
            "player1_goals": 2,
            "player2_goals": 1,
            "team1": "Barcelona",
            "team2": "Real Madrid",
            "tournament_id": tournament_id
        }
        
        match_response = client.post("/api/v1/matches/", json=match_data)
        assert match_response.status_code == 200
        
        # Get tournament matches
        matches_response = client.get(f"/api/v1/tournaments/{tournament_id}/matches")
        assert matches_response.status_code == 200
        matches = matches_response.json()
        
        assert len(matches) == 1
        assert matches[0]["tournament_name"] == created_tournament["name"]

    def test_tournament_lifecycle(self, client: TestClient):
        """Test complete tournament lifecycle: create, read"""
        # Create
        create_data = {"name": "Lifecycle Tournament", "description": "Test tournament"}
        create_response = client.post("/api/v1/tournaments/", json=create_data)
        assert create_response.status_code == 200
        tournament = create_response.json()
        tournament_id = tournament["id"]
        
        # Read - via get all
        all_response = client.get("/api/v1/tournaments/")
        assert all_response.status_code == 200
        all_tournaments = all_response.json()
        assert len(all_tournaments) == 1
        assert all_tournaments[0]["name"] == create_data["name"]
        
        # Read - tournament matches
        matches_response = client.get(f"/api/v1/tournaments/{tournament_id}/matches")
        assert matches_response.status_code == 200
        matches_data = matches_response.json()
        assert matches_data["items"] == []
        assert matches_data["total"] == 0

    def test_get_tournament_matches_pagination(self, client: TestClient, created_tournament):
        """Test pagination for tournament matches"""
        tournament_id = created_tournament["id"]
        
        # Test default pagination (page 1, default page size)
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert data["page"] == 1
        assert data["page_size"] == 50  # Default page size
        
        # Test custom page size
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches?page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 10
        
        # Test custom page number
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches?page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        
        # Test invalid page number
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches?page=0")
        assert response.status_code == 422  # Validation error
        
        # Test invalid page size
        response = client.get(f"/api/v1/tournaments/{tournament_id}/matches?page_size=0")
        assert response.status_code == 422  # Validation error 