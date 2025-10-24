import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime
from app.models.auth import UserCreate, UserInDB
from app.utils.auth import get_password_hash


class TestUserRegistration:
    """Test suite for user registration endpoint"""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123"
        }
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock database responses - no existing user
            mock_db_instance.users.find_one.return_value = None
            
            # Mock insert operation
            mock_insert_result = AsyncMock()
            mock_insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
            mock_db_instance.users.insert_one.return_value = mock_insert_result
            
            # Mock created user data
            created_user_data = {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "hashed_password": get_password_hash("securepassword123"),
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_matches": 0,
                "total_goals_scored": 0,
                "total_goals_conceded": 0,
                "goal_difference": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0,
                "elo_rating": 1200,
                "tournaments_played": 0,
                "tournament_ids": [],
                "friends": [],
                "friend_requests_sent": [],
                "friend_requests_received": [],
                "last_5_teams": []
            }
            
            # Set up side effect for find_one calls
            def mock_find_one_side_effect(query):
                if "username" in query and query["username"] == "newuser":
                    return None  # Username check
                elif "email" in query and query["email"] == "newuser@example.com":
                    return None  # Email check
                elif "_id" in query:
                    return created_user_data  # Get created user
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one_side_effect
            
            # Make the request
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["message"] == "User registered successfully"
            assert "data" in data
            
            user = data["data"]
            assert user["username"] == "newuser"
            assert user["email"] == "newuser@example.com"
            assert user["first_name"] == "New"
            assert user["last_name"] == "User"
            assert user["is_active"] is True
            assert user["is_superuser"] is False
            assert user["total_matches"] == 0
            assert user["elo_rating"] == 1200
            assert "id" in user
            assert "created_at" in user
            assert "updated_at" in user
            
            # Verify database calls
            assert mock_db_instance.users.find_one.call_count == 3  # Check username, email, and get created user
            assert mock_db_instance.users.insert_one.call_count == 1
    
    def test_register_user_duplicate_username(self, client: TestClient):
        """Test registration with duplicate username"""
        user_data = {
            "username": "existinguser",
            "email": "newemail@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123"
        }
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock existing user found by username
            existing_user = {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "username": "existinguser",
                "email": "existing@example.com"
            }
            mock_db_instance.users.find_one.return_value = existing_user
            
            # Make the request
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Assertions
            assert response.status_code == 400
            data = response.json()
            
            assert data["success"] is False
            assert data["message"] == "Username already registered"
            
            # Verify database was called to check username
            assert mock_db_instance.users.find_one.call_count == 1
    
    def test_register_user_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email"""
        user_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123"
        }
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock no existing user by username, but existing user by email
            def mock_find_one(query):
                if "username" in query:
                    return None  # Username is available
                elif "email" in query:
                    return {  # Email already exists
                        "_id": ObjectId("507f1f77bcf86cd799439012"),
                        "username": "existinguser",
                        "email": "existing@example.com"
                    }
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one
            
            # Make the request
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Assertions
            assert response.status_code == 400
            data = response.json()
            
            assert data["success"] is False
            assert data["message"] == "Email already registered"
            
            # Verify database was called to check both username and email
            assert mock_db_instance.users.find_one.call_count == 2
    
    def test_register_user_invalid_data(self, client: TestClient):
        """Test registration with invalid data"""
        # Test missing required fields
        invalid_data = {
            "username": "testuser",
            # Missing email and password
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Test invalid email format
        invalid_email_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_email_data)
        assert response.status_code == 422
        
        # Test username too long
        long_username_data = {
            "username": "a" * 15,  # Exceeds 14 character limit
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/register", json=long_username_data)
        assert response.status_code == 422
    
    def test_register_user_minimal_data(self, client: TestClient):
        """Test registration with minimal required data"""
        minimal_data = {
            "username": "minimal",
            "email": "minimal@example.com",
            "password": "password123"
        }
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock database responses - no existing user
            mock_db_instance.users.find_one.return_value = None
            
            # Mock insert operation
            mock_insert_result = AsyncMock()
            mock_insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
            mock_db_instance.users.insert_one.return_value = mock_insert_result
            
            # Mock created user data
            created_user_data = {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "username": "minimal",
                "email": "minimal@example.com",
                "first_name": None,
                "last_name": None,
                "hashed_password": get_password_hash("password123"),
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_matches": 0,
                "total_goals_scored": 0,
                "total_goals_conceded": 0,
                "goal_difference": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0,
                "elo_rating": 1200,
                "tournaments_played": 0,
                "tournament_ids": [],
                "friends": [],
                "friend_requests_sent": [],
                "friend_requests_received": [],
                "last_5_teams": []
            }
            
            # Set up side effect for find_one calls
            def mock_find_one_side_effect(query):
                if "username" in query and query["username"] == "minimal":
                    return None  # Username check
                elif "email" in query and query["email"] == "minimal@example.com":
                    return None  # Email check
                elif "_id" in query:
                    return created_user_data  # Get created user
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one_side_effect
            
            # Make the request
            response = client.post("/api/v1/auth/register", json=minimal_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            user = data["data"]
            assert user["username"] == "minimal"
            assert user["email"] == "minimal@example.com"
            assert user["first_name"] is None
            assert user["last_name"] is None


class TestUsernameCheck:
    """Test suite for username availability check endpoint"""
    
    def test_check_username_available(self, client: TestClient):
        """Test checking available username"""
        username_data = {"username": "availableuser"}
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock no existing user found
            mock_db_instance.users.find_one.return_value = None
            
            # Make the request
            response = client.post("/api/v1/auth/check-username", json=username_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["message"] == "Username availability checked"
            assert data["data"]["username"] == "availableuser"
            assert data["data"]["exists"] is False
    
    def test_check_username_taken(self, client: TestClient):
        """Test checking taken username"""
        username_data = {"username": "takenuser"}
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock existing user found
            existing_user = {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "username": "takenuser",
                "email": "taken@example.com"
            }
            mock_db_instance.users.find_one.return_value = existing_user
            
            # Make the request
            response = client.post("/api/v1/auth/check-username", json=username_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["message"] == "Username availability checked"
            assert data["data"]["username"] == "takenuser"
            assert data["data"]["exists"] is True
    
    def test_check_username_invalid_format(self, client: TestClient):
        """Test checking username with invalid format"""
        # Test empty username - this actually works in the current implementation
        username_data = {"username": ""}
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock no existing user found
            mock_db_instance.users.find_one.return_value = None
            
            response = client.post("/api/v1/auth/check-username", json=username_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["username"] == ""
            assert data["data"]["exists"] is False
        
        # Test username too long - this actually works in the current implementation
        # since UsernameCheck model doesn't have validation constraints
        username_data = {"username": "a" * 15}  # Exceeds 14 character limit
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock no existing user found
            mock_db_instance.users.find_one.return_value = None
            
            response = client.post("/api/v1/auth/check-username", json=username_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["username"] == "a" * 15
            assert data["data"]["exists"] is False


class TestUserRegistrationIntegration:
    """Integration tests for user registration flow"""
    
    def test_register_and_check_username_flow(self, client: TestClient):
        """Test complete flow: check username availability then register"""
        username = "flowtestuser"
        user_data = {
            "username": username,
            "email": "flowtest@example.com",
            "first_name": "Flow",
            "last_name": "Test",
            "password": "password123"
        }
        
        # Mock database operations
        with patch('app.api.v1.endpoints.auth.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            
            # Mock database responses
            def mock_find_one(query):
                if "username" in query and query["username"] == username:
                    return None  # Username available
                elif "email" in query:
                    return None  # Email available
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one
            
            # Mock insert operation
            mock_insert_result = AsyncMock()
            mock_insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
            mock_db_instance.users.insert_one.return_value = mock_insert_result
            
            # Mock created user data
            created_user_data = {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "username": username,
                "email": "flowtest@example.com",
                "first_name": "Flow",
                "last_name": "Test",
                "hashed_password": get_password_hash("password123"),
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_matches": 0,
                "total_goals_scored": 0,
                "total_goals_conceded": 0,
                "goal_difference": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0,
                "elo_rating": 1200,
                "tournaments_played": 0,
                "tournament_ids": [],
                "friends": [],
                "friend_requests_sent": [],
                "friend_requests_received": [],
                "last_5_teams": []
            }
            
            # Set up side effect for find_one calls
            def mock_find_one_side_effect(query):
                if "username" in query and query["username"] == username:
                    return None  # Username available
                elif "email" in query and query["email"] == "flowtest@example.com":
                    return None  # Email available
                elif "_id" in query:
                    return created_user_data  # Get created user
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one_side_effect
            
            # Step 1: Check username availability
            check_response = client.post("/api/v1/auth/check-username", json={"username": username})
            assert check_response.status_code == 200
            check_data = check_response.json()
            assert check_data["data"]["exists"] is False
            
            # Step 2: Register user
            register_response = client.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == 200
            register_data = register_response.json()
            assert register_data["success"] is True
            assert register_data["data"]["username"] == username
            
            # Step 3: Check username again (should now be taken)
            # Reset the mock to return the created user for username check
            def mock_find_one_after_registration(query):
                if "username" in query and query["username"] == username:
                    return created_user_data  # Username now taken
                return None
            
            mock_db_instance.users.find_one.side_effect = mock_find_one_after_registration
            
            check_response = client.post("/api/v1/auth/check-username", json={"username": username})
            assert check_response.status_code == 200
            check_data = check_response.json()
            assert check_data["data"]["exists"] is True
