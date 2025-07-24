from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_elo_ratings(player1_rating: int, player2_rating: int, player1_goals: int, player2_goals: int) -> tuple[int, int]:
    """
    Calculate new ELO ratings for both players after a match.
    
    Args:
        player1_rating: Current ELO rating of player 1
        player2_rating: Current ELO rating of player 2
        player1_goals: Goals scored by player 1
        player2_goals: Goals scored by player 2
    
    Returns:
        tuple: (new_player1_rating, new_player2_rating)
    """
    # Determine match outcome
    if player1_goals > player2_goals:
        # Player 1 wins
        actual_score_player1 = 1.0
        actual_score_player2 = 0.0
    elif player1_goals < player2_goals:
        # Player 2 wins
        actual_score_player1 = 0.0
        actual_score_player2 = 1.0
    else:
        # Draw
        actual_score_player1 = 0.5
        actual_score_player2 = 0.5
    
    # Calculate expected scores using ELO formula
    expected_score_player1 = 1.0 / (1.0 + 10 ** ((player2_rating - player1_rating) / 400.0))
    expected_score_player2 = 1.0 / (1.0 + 10 ** ((player1_rating - player2_rating) / 400.0))
    
    # Calculate new ratings
    new_rating_player1 = player1_rating + settings.ELO_K_FACTOR * (actual_score_player1 - expected_score_player1)
    new_rating_player2 = player2_rating + settings.ELO_K_FACTOR * (actual_score_player2 - expected_score_player2)
    
    # Round to nearest integer
    new_rating_player1 = round(new_rating_player1)
    new_rating_player2 = round(new_rating_player2)
    
    logger.debug(
        f"ELO calculation: Player1({player1_rating}->{new_rating_player1}) vs "
        f"Player2({player2_rating}->{new_rating_player2}) "
        f"Score: {player1_goals}-{player2_goals}"
    )
    
    return new_rating_player1, new_rating_player2


def calculate_elo_change(player1_rating: int, player2_rating: int, player1_goals: int, player2_goals: int) -> tuple[int, int]:
    """
    Calculate ELO rating changes for both players after a match.
    
    Args:
        player1_rating: Current ELO rating of player 1
        player2_rating: Current ELO rating of player 2
        player1_goals: Goals scored by player 1
        player2_goals: Goals scored by player 2
    
    Returns:
        tuple: (player1_elo_change, player2_elo_change)
    """
    new_rating_player1, new_rating_player2 = calculate_elo_ratings(
        player1_rating, player2_rating, player1_goals, player2_goals
    )
    
    player1_change = new_rating_player1 - player1_rating
    player2_change = new_rating_player2 - player2_rating
    
    return player1_change, player2_change 