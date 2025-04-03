from dataclasses import asdict
import json
from typing import List 
from functools import wraps
import inspect
from .prompter import OpenAIPrompter
from .examples import (
    DTR_EXAMPLES, DTR_MAIN_HEADER,RESP_EXAMPLES, RESP_MAIN_HEADER, STYLIZE_EXAMPLES, 
    STYLIZE_MAIN_HEADER, SYSTEM_PROMPT, VALIDATE_EXAMPLES, VALIDATE_MAIN_HEADER
)
from .enums_dcs import (
    RespondBM, StylizerBM, DecideToRespondBM, ValidateResponseBM, 
)
import sys
sys.path.append("../../")
from utils.states import PlayerState, GameState
from utils.file_io import SequentialAssigner
from utils.constants import (
    NAMES_PATH, NAMES_INDEX_PATH, 
    COLORS_PATH, COLORS_INDEX_PATH
    )
from utils.logging_utils import StandAloneLogger


# def handle_errors():
#     def decorator(func):
#         @wraps(func)
#         def wrapper(self, *args, **kwargs):
#             try:
#                 return func(self, *args, **kwargs)
#             except Exception as e:
#                 if getattr(self, 'debug_bool', False):
#                     raise

#                 # Attempt to get the `response_json` from the frame
#                 frame = inspect.currentframe().f_back.f_back
#                 response_json = frame.f_locals.get("response_json", None)

#                 if hasattr(self, 'logger'):
#                     if response_json is not None:
#                         self.logger.error(f"{func.__name__} – LLM Response: {response_json}")
#                     self.logger.error(f"{func.__name__} – Error: {e}")

#                 return f"Error in {func.__name__}: {str(e)}\nLLM Response: {response_json}" if response_json else str(e)
#         return wrapper
#     return decorator

class AIPlayer:
    def __init__(
            self,
            player_to_steal: PlayerState, 
            system_prompt: str = SYSTEM_PROMPT,
            debug_bool: bool = False):
        self.humans_messages = []
        self.stolen_player_code_name = player_to_steal.code_name
        # self.color_name = SequentialAssigner(
        #     COLORS_PATH, COLORS_INDEX_PATH, "colors").assign()  # Assign a new color name
        self.code_name_assigner = SequentialAssigner(NAMES_PATH, NAMES_INDEX_PATH, "code_names")
        self.color_assigner = SequentialAssigner(COLORS_PATH, COLORS_INDEX_PATH, "colors")
        self.player_state = self._steal_player_state(player_to_steal)
        self.system_prompt = system_prompt

        self.debug_bool = debug_bool

        # Initialize game state
        self.game_state = None
        self.logger = self._init_logger()
        
        # Prompter Dictionary
        # Updated Prompter Dictionary with prompt_headers
        self.prompter_dict = {
            "decide_to_respond": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=DTR_EXAMPLES,
                prompt_headers={"minutes": "Minutes:\n", "game_state": "Game State:\n"},  # Add prompt headers
                output_format=DecideToRespondBM,
                main_prompt_header=DTR_MAIN_HEADER
            ),
            "generate_response": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=RESP_EXAMPLES,
                prompt_headers={"minutes": "Minutes:\n", "game_state": "Game State:\n"},  # Add prompt headers
                output_format=RespondBM,
                main_prompt_header=RESP_MAIN_HEADER
            ),
            "stylize_response": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=STYLIZE_EXAMPLES,
                prompt_headers={"response": "Response:\n", "examples": "Examples:\n"},  # Add prompt headers
                output_format=StylizerBM,
                main_prompt_header=STYLIZE_MAIN_HEADER
            ),
            "validate_response": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=VALIDATE_EXAMPLES,
                prompt_headers={"response": "Response:\n"},  # Add prompt headers
                output_format=ValidateResponseBM,
                main_prompt_header=VALIDATE_MAIN_HEADER
            )
        }


    # @handle_errors()
    def decide_to_respond(self, minutes: List[str]):
        """Decide whether the AI should respond."""
        last_msg = minutes[-1] if minutes else None
        if last_msg and last_msg.startswith(f"{self.stolen_player_code_name}:"):
            self.humans_messages.append(last_msg.split(":", 1)[1].strip())

        response_json = self.prompter_dict["decide_to_respond"].get_completion({
            "minutes": "\n".join(minutes),
            "game_state": json.dumps(self.game_state.to_dict())
        })
        self.logger.info(f"DTR JSON: {response_json}")
        decision = DecideToRespondBM.model_validate_json(json.dumps(response_json))

        if decision.respond_bool:
            return self.generate_response(minutes)
        return "No response needed."

    # @handle_errors()
    def generate_response(self, minutes: List[str]):
        """Generate a response based on the game state and chat."""
        response_json = self.prompter_dict["generate_response"].get_completion({
            "minutes": "\n".join(minutes),
            "game_state": json.dumps(self.game_state.to_dict())
        })
        self.logger.info(f"Generate Response JSON: {response_json}")
        response = RespondBM.model_validate_json(json.dumps(response_json)).response
        return self.stylize_response(response)

    # @handle_errors()
    def stylize_response(self, response: str):
        """Stylize the response to match the player's speech style."""
        response_json = self.prompter_dict["stylize_response"].get_completion({
            "response": response,
            "examples": "\n".join(self.humans_messages)
        })
        self.logger.info(f"Stylize Response JSON: {response_json}")
        styled_response = StylizerBM.model_validate_json(json.dumps(response_json)).output_text
        return self.validate_response(styled_response)

    # @handle_errors()
    def validate_response(self, styled_response: str):
        """Validate the generated response to ensure it fits the context."""
        response_json = self.prompter_dict["validate_response"].get_completion({
            "response": styled_response
        })
        self.logger.info(f"Validate Response JSON: {response_json}")
        validation = ValidateResponseBM.model_validate_json(json.dumps(response_json))

        if validation.valid:
            return styled_response
        return f"Generated response deemed invalid: {validation.reasoning}"

    def _steal_player_state(self, player_state_to_steal: PlayerState) -> PlayerState:
        """Creates a new player state based on the given one."""
        
        return PlayerState(
            first_name=player_state_to_steal.first_name,
            last_initial=player_state_to_steal.last_initial,
            code_name=self.code_name_assigner.assign(),  # Assign a new code name
            color_name=self.color_assigner.assign(),  # Assign a new color name
            grade=player_state_to_steal.grade,
            favorite_food=player_state_to_steal.favorite_food,
            favorite_animal=player_state_to_steal.favorite_animal,
            hobby=player_state_to_steal.hobby,
            extra_info=player_state_to_steal.extra_info,
            written_to_file=True,
            lobby_id=player_state_to_steal.lobby_id,
            is_human=False,  # This player is not human
        )
    def _init_logger(self):
        logger = StandAloneLogger(
            log_path=f"./logs/runtime/lobbies/lobby_{self.player_state.lobby_id}/players/{self.player_state.code_name}.log",
            clear=True,
            init=True
        )
        return logger
    
    def initialize_game_state(self, game_state: GameState):
        """Initialize the game state."""
        self.game_state = game_state
        self.logger.info(f"Game state initialized with players: {self.stolen_player_code_name}")
