# ELO Rating Implementation

This document describes the ELO rating system implementation for the FIFA Rivalry Tracker.

## Overview

The ELO rating system has been integrated into the match recording functionality to provide a fair and dynamic ranking system for players. ELO ratings are automatically calculated and updated whenever matches are recorded, updated, or deleted.

## Implementation Details

### 1. ELO Calculation Module (`app/utils/elo.py`)

The core ELO calculation logic is implemented in the `app/utils/elo.py` module with two main functions:

- `calculate_elo_ratings(player1_rating, player2_rating, player1_goals, player2_goals)`: Calculates new ELO ratings for both players after a match
- `calculate_elo_change(player1_rating, player2_rating, player1_goals, player2_goals)`: Calculates the ELO rating changes for both players

### 2. Configuration (`app/config.py`)

ELO settings are configurable through the application settings:

```python
# ELO Rating
DEFAULT_ELO_RATING: int = 1200  # Starting ELO rating for new players
ELO_K_FACTOR: int = 32          # K-factor determines rating change magnitude
```

### 3. Database Integration

ELO ratings are stored in the player documents in the `elo_rating` field. The field is initialized to 1200 for new players and updated after each match.

### 4. Match Operations

#### Creating a Match (`POST /api/v1/matches/`)

When a new match is recorded:
1. Current ELO ratings are retrieved for both players
2. New ELO ratings are calculated based on match outcome
3. Player statistics and ELO ratings are updated in the database

#### Updating a Match (`PUT /api/v1/matches/{match_id}`)

When a match is updated:
1. The old match result is reverted (ELO ratings are calculated as if the old result never happened)
2. New ELO ratings are calculated with the updated match result
3. Player statistics and ELO ratings are updated accordingly

#### Deleting a Match (`DELETE /api/v1/matches/{match_id}`)

When a match is deleted:
1. The match result is reverted (ELO ratings are calculated as if the match never happened)
2. Player statistics and ELO ratings are updated to remove the match's impact

## ELO Formula

The implementation uses the standard ELO rating formula:

1. **Expected Score Calculation**:
   ```
   Expected Score = 1 / (1 + 10^((opponent_rating - player_rating) / 400))
   ```

2. **Actual Score Assignment**:
   - Win: 1.0
   - Draw: 0.5
   - Loss: 0.0

3. **New Rating Calculation**:
   ```
   New Rating = Current Rating + K * (Actual Score - Expected Score)
   ```

4. **K-Factor**: Currently set to 32, which provides moderate rating volatility

## Key Features

### Zero-Sum Property
The ELO system maintains a zero-sum property where the total rating points in the system remain constant. When one player gains rating points, their opponent loses an equal amount.

### Upset Bonuses
Lower-rated players who defeat higher-rated opponents gain more rating points than expected, while higher-rated players who lose to lower-rated opponents lose more points.

### Expected Win Penalties
Higher-rated players who defeat lower-rated opponents gain fewer rating points than expected, as the system considers this an "expected" outcome.

### Draw Handling
When players draw, both players experience minimal rating changes, with the exact change depending on their rating difference.

## Testing

The implementation includes comprehensive tests in `app/tests/test_elo.py` that verify:

- Basic win/loss scenarios
- Draw scenarios
- Upset wins (lower-rated player wins)
- Expected wins (higher-rated player wins)
- Zero-sum property maintenance
- K-factor impact on rating changes

## Example Calculations

### Equal Ratings (1200 vs 1200)
- **Player 1 wins 3-1**: Player 1 gains +16, Player 2 loses -16
- **Player 2 wins 1-3**: Player 1 loses -16, Player 2 gains +16
- **Draw 2-2**: Both players experience 0 change

### Upset Win (1000 vs 1400)
- **Lower-rated player wins 3-1**: Player 1 gains +29, Player 2 loses -29

### Expected Win (1400 vs 1000)
- **Higher-rated player wins 3-1**: Player 1 gains +3, Player 2 loses -3

## Configuration Options

The ELO system can be customized by modifying the settings in `app/config.py`:

- `DEFAULT_ELO_RATING`: Starting rating for new players (default: 1200)
- `ELO_K_FACTOR`: Rating change magnitude (default: 32)
  - Higher K-factor = more volatile ratings
  - Lower K-factor = more stable ratings

## Integration Points

The ELO system is integrated into:

1. **Player Registration**: New players start with the default ELO rating
2. **Match Recording**: ELO ratings are updated when matches are created
3. **Match Updates**: ELO ratings are recalculated when matches are modified
4. **Match Deletion**: ELO ratings are reverted when matches are deleted
5. **Player Statistics**: ELO ratings are included in player data responses

## Future Enhancements

Potential improvements to consider:

1. **Dynamic K-Factor**: Adjust K-factor based on player experience or rating range
2. **Tournament Weighting**: Give tournament matches different weightings
3. **Rating Decay**: Implement rating decay for inactive players
4. **Rating Bands**: Different K-factors for different rating ranges
5. **Match History**: Track ELO rating changes over time 