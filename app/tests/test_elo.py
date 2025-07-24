import pytest
from app.utils.elo import calculate_elo_ratings, calculate_elo_change
from app.config import settings


class TestELOCalculation:
    """Test ELO rating calculations"""
    
    def test_elo_win_scenario(self):
        """Test ELO calculation when player 1 wins"""
        player1_rating = 1200
        player2_rating = 1200
        player1_goals = 3
        player2_goals = 1
        
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Player 1 should gain rating, player 2 should lose rating
        assert new_player1_rating > player1_rating
        assert new_player2_rating < player2_rating
        
        # Total rating should remain the same (zero-sum)
        total_before = player1_rating + player2_rating
        total_after = new_player1_rating + new_player2_rating
        assert total_before == total_after
    
    def test_elo_loss_scenario(self):
        """Test ELO calculation when player 1 loses"""
        player1_rating = 1200
        player2_rating = 1200
        player1_goals = 1
        player2_goals = 3
        
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Player 1 should lose rating, player 2 should gain rating
        assert new_player1_rating < player1_rating
        assert new_player2_rating > player2_rating
        
        # Total rating should remain the same (zero-sum)
        total_before = player1_rating + player2_rating
        total_after = new_player1_rating + new_player2_rating
        assert total_before == total_after
    
    def test_elo_draw_scenario(self):
        """Test ELO calculation when players draw"""
        player1_rating = 1200
        player2_rating = 1200
        player1_goals = 2
        player2_goals = 2
        
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Both players should have minimal rating change
        assert abs(new_player1_rating - player1_rating) < 5
        assert abs(new_player2_rating - player2_rating) < 5
        
        # Total rating should remain the same (zero-sum)
        total_before = player1_rating + player2_rating
        total_after = new_player1_rating + new_player2_rating
        assert total_before == total_after
    
    def test_elo_upset_win(self):
        """Test ELO calculation when lower-rated player wins (upset)"""
        player1_rating = 1000  # Lower rated
        player2_rating = 1400  # Higher rated
        player1_goals = 3
        player2_goals = 1
        
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Lower-rated player should gain more rating for upset win
        player1_gain = new_player1_rating - player1_rating
        player2_loss = player2_rating - new_player2_rating
        
        assert player1_gain > 0
        assert player2_loss > 0
        assert player1_gain > player2_loss  # Upset should give more points
        
        # Total rating should remain the same (zero-sum)
        total_before = player1_rating + player2_rating
        total_after = new_player1_rating + new_player2_rating
        assert total_before == total_after
    
    def test_elo_expected_win(self):
        """Test ELO calculation when higher-rated player wins (expected)"""
        player1_rating = 1400  # Higher rated
        player2_rating = 1000  # Lower rated
        player1_goals = 3
        player2_goals = 1
        
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Higher-rated player should gain less rating for expected win
        player1_gain = new_player1_rating - player1_rating
        player2_loss = player2_rating - new_player2_rating
        
        assert player1_gain > 0
        assert player2_loss > 0
        assert player1_gain < player2_loss  # Expected win should give fewer points
        
        # Total rating should remain the same (zero-sum)
        total_before = player1_rating + player2_rating
        total_after = new_player1_rating + new_player2_rating
        assert total_before == total_after
    
    def test_elo_change_function(self):
        """Test the calculate_elo_change function"""
        player1_rating = 1200
        player2_rating = 1200
        player1_goals = 3
        player2_goals = 1
        
        player1_change, player2_change = calculate_elo_change(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        # Changes should sum to zero (zero-sum game)
        assert player1_change + player2_change == 0
        
        # Player 1 should gain, player 2 should lose
        assert player1_change > 0
        assert player2_change < 0
        
        # Verify the changes match the full calculation
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        assert player1_change == new_player1_rating - player1_rating
        assert player2_change == new_player2_rating - player2_rating
    
    def test_elo_k_factor_impact(self):
        """Test that K-factor affects rating changes appropriately"""
        player1_rating = 1200
        player2_rating = 1200
        player1_goals = 3
        player2_goals = 1
        
        # Calculate with current K-factor
        new_player1_rating, new_player2_rating = calculate_elo_ratings(
            player1_rating, player2_rating, player1_goals, player2_goals
        )
        
        current_change = new_player1_rating - player1_rating
        
        # The change should be related to the K-factor
        # For equal ratings, the expected score is 0.5, actual is 1.0
        # So the change should be approximately K * (1.0 - 0.5) = K * 0.5
        expected_change = settings.ELO_K_FACTOR * 0.5
        
        assert abs(current_change - expected_change) < 2  # Allow for rounding 