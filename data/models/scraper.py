from typing import List, Optional
from pydantic import BaseModel, Field

class PlayerSeasonStats(BaseModel):
    """
    Data model for a single season of a player's statistics.
    Corresponds to one row in the player_season_stats table.
    """
    season_year: str
    games_played: Optional[int] = None
    minutes_played: Optional[float] = None
    points_per_game: Optional[float] = Field(None, alias='Points Per Game')
    rebounds_per_game: Optional[float] = Field(None, alias='Rebounds Per Game')
    assists_per_game: Optional[float] = Field(None, alias='Assists Per Game')
    blocks_per_game: Optional[float] = Field(None, alias='Blocks Per Game')
    steals_per_game: Optional[float] = Field(None, alias='Steals Per Game')
    field_goal_percentage: Optional[float] = Field(None, alias='Field Goal Percentage')
    three_point_percentage: Optional[float] = Field(None, alias='3 Point Field Goal Percentage')
    free_throw_percentage: Optional[float] = Field(None, alias='Free Throw Percentage')

    class Config:
        # Allows creating the model from a dictionary where keys might not match field names exactly
        populate_by_name = True

class Player(BaseModel):
    """
    Data model for a player's static information.
    Corresponds to one row in the players table.
    """
    player_name: str = Field(..., alias='Player Name')
    profile_url: str = Field(..., alias='247Sports Profile URL')
    position: Optional[str] = 'N/A'
    rating: Optional[str] = 'N/A'
    status: Optional[str] = 'N/A'
    highschool: Optional[str] = 'N/A'
    height: Optional[str] = 'N/A'
    weight: Optional[str] = 'N/A'
    old_school: Optional[str] = Field('N/A', alias='Old School')
    new_school: Optional[str] = Field('N/A', alias='New School')
    
    # This field will hold the stats during the transformation phase
    seasonal_stats: List[PlayerSeasonStats] = []

    class Config:
        populate_by_name = True
