from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class ScreenState(Enum):
    INTRO = 0
    SETUP = 1
    CHAT = 2
    VOTE = 3
    SCORE = 4
    

@dataclass
class PlayerState:
    lobby_id: str
    first_name: str
    last_initial: str
    code_name: str
    grade: str
    favorite_food: str
    favorite_animal: str
    hobby: str
    extra_info: str
    is_human: bool 
    color_name: str     
    starttime: str = "" # Start time of the game
    voted: bool = False # Flag to indicate if the player has voted
    ai_doppleganger: Optional[AIPlayer] = None # type: ignore
    written_to_file: bool = False # Flag to indicate if the player has been written to a file
    timekeeper: bool = False # Flag to indicate if the player is a timekeeper
    still_in_game: bool = True # Flag to indicate if the player is still in the game

    def to_dict(self) -> dict:
        return {
            "lobby_id": self.lobby_id,
            "first_name": self.first_name,
            "last_initial": self.last_initial,
            "code_name": self.code_name,
            "grade": self.grade,
            "favorite_food": self.favorite_food,
            "favorite_animal": self.favorite_animal,
            "hobby": self.hobby,
            "extra_info": self.extra_info,
            "color_name": self.color_name,
            "starttime": self.starttime.isoformat() if isinstance(self.starttime, datetime) else self.starttime,
        }
    def serialize_player(self, player):
        """Convert a player object to a JSON-serializable dictionary."""
        if isinstance(player, PlayerState):
            return {
                "code_name": player.code_name,
                "is_human": player.is_human,
                "still_in_game": player.still_in_game,
            }
        return str(player) 
    def to_persona(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_initial": self.last_initial,
            "code_name": self.code_name,
            "grade": self.grade,
            "favorite_food": self.favorite_food,
            "favorite_animal": self.favorite_animal,
            "hobby": self.hobby,
            "extra_info": self.extra_info,
        }

@dataclass
class GameState:
    round_number: int
    players: List[PlayerState] = field(default_factory=list)
    players_voted_off: List[PlayerState] = field(default_factory=list)
    last_vote_outcome: str = ""     # The outcome of the last vote
    chat_log_path: str = ""         # Path to the chat log file
    voting_path: str = ""           # Path to the voting file
    start_time_path: str = ""       # Path to the start time file
    player_path: str = ""           # Path to the player file
    chat_log: str = ""              # Chat log content
    voting_log: str = ""            # Voting log content
    chat_complete: bool = False      # Flag to indicate if the chat is complete
    voting_complete: bool = False    # Flag to indicate if the voting is complete
    round_complete: bool = False
    number_of_human_players: int = 0
    ice_asked: int = 0
    icebreakers: list = field(default_factory=lambda: ["your_values"])

    def to_dict(self) -> dict:
        def serialize(value):
            if isinstance(value, datetime):
                return value.isoformat()
            return value

        return {
            "round_number": self.round_number,
            "players": [player.to_dict() if isinstance(player, PlayerState) else player for player in self.players],
            "players_voted_off": self.players_voted_off,
            "last_vote_outcome": self.last_vote_outcome,
            "chat_log_path": self.chat_log_path,
            "voting_path": self.voting_path,
            "start_time_path": self.start_time_path,
            "player_path": self.player_path,
            "chat_log": self.chat_log,
            "voting_log": self.voting_log,
            "chat_complete": self.chat_complete,
            "voting_complete": self.voting_complete,
            "round_complete": self.round_complete,
            "number_of_human_players": self.number_of_human_players,
            "ice_asked": self.ice_asked,
            "icebreakers": self.icebreakers,
            # Example datetime field
            "start_time": serialize(self.start_time) if hasattr(self, "start_time") else None
        }


