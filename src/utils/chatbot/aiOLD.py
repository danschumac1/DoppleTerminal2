from dataclasses import asdict
import json
from typing import List, Tuple, Union
from functools import wraps
import inspect
from .prompter import OpenAIPrompter
from utils.logging_utils import StandAloneLogger
from .examples import (
    GENERIC_PROMPT_HEADERS, CHOOSE_ACTION_MAIN_HEADER, CHOSE_ACTION_EXAMPLES, 
    DEFEND_MAIN_HEADER, DEFEND_EXAMPLES, ACCUSE_MAIN_HEADER, ACCUSE_EXAMPLES, 
    DTR_EXAMPLES, DTR_MAIN_HEADER,GSU_HEADERS, INTRO_EXAMPLES, INTRO_MAIN_HEADER, JOKE_MAIN_HEADER,
    JOKE_EXAMPLES, OTHER_EXAMPLES, OTHER_MAIN_HEADER, QUESTION_MAIN_HEADER, QUESTION_EXAMPLES, SIMPLE_PHRASE_MAIN_HEADER, 
    SIMPLE_PHRASE_EXAMPLES, GSU_MAIN_HEADER, GSU_EXAMPLES, STYLIZER_EXAMPLES, STYLIZER_HEADERS, 
    STYLIZER_MAIN_HEADER, DEFAULT_SYSTEM_PROMPT
)
from .enums_dcs import (
    IntroBM, JokeBM, QuestionBM, SimplePhraseBM, StylizerBM, Team, ActionOptionBM, DecideToRespondBM, 
    DefendYourselfBM, AccusePlayerBM, GameSummaryBM
)
import sys
sys.path.append("../../")
from utils.states import ScreenState, PlayerState, GameState
from utils.constants import COLOR_DICT, NAMES_PATH, NAMES_INDEX_PATH, COLORS_PATH, COLORS_INDEX_PATH
from utils.file_io import SequentialAssigner

# TODO -> use the sequential assigner to assign a code name and color to the AI player
# TODO -> use the AI player to play the game
# TODO -> connect multiple players to the game

def handle_errors():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if getattr(self, 'debug_bool', False):
                    raise

                # Attempt to get the `response_json` from the frame
                frame = inspect.currentframe().f_back.f_back

                response_json = frame.f_locals.get("response_json", None)

                if hasattr(self, 'logger'):
                    if response_json is not None:
                        self.logger.error(f"{func.__name__} – LLM Response: {response_json}")
                    self.logger.error(f"{func.__name__} – Error: {e}")

                return f"Error in {func.__name__}: {str(e)}\nLLM Response: {response_json}" if response_json else str(e)

        return wrapper
    return decorator


class AIPlayer:
    def __init__(
            self, players_code_names: List[str],
            player_to_steal: PlayerState, 
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            debug_bool: bool = False):
        self.logger = None # filled in later
        self.prompt_tail = None
        self.players_code_names = players_code_names
        self.team = Team.HUMAN
        self.voting_history = []
        self.has_introduced = False
        self.is_accused = False
        self.is_questioned = False
        self.humans_introduced = 0
        self.player_state = self._steal_player_state(player_to_steal)
        self.origin_code_name = player_to_steal.code_name if player_to_steal else "N/A"
        self.system_prompt = system_prompt + json.dumps(asdict(self.player_state))
        self.game_summary = self._initialize_game_summary()
        self.debug_bool = debug_bool
        self.player_minutes = [self.player_state.extra_info] if self.player_state.extra_info else []

        # Initialize custom prompter_dict
        self.prompter_dict = {
            "decide_to_respond": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=DTR_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=DecideToRespondBM,
                main_prompt_header=DTR_MAIN_HEADER
            ),
            
            "choose_action": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=CHOSE_ACTION_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=ActionOptionBM,
                main_prompt_header=CHOOSE_ACTION_MAIN_HEADER
            ),
            "introduce": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=INTRO_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=IntroBM,
                main_prompt_header=INTRO_MAIN_HEADER,
                temperature=0.5
            ),
            "stylizer": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=STYLIZER_EXAMPLES,
                prompt_headers=STYLIZER_HEADERS,
                output_format=StylizerBM,
                main_prompt_header=STYLIZER_MAIN_HEADER
            ),
            "defend": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=DEFEND_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=DefendYourselfBM,
                main_prompt_header=DEFEND_MAIN_HEADER,
                temperature=0.5
            ),
            "accuse": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ACCUSE_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=AccusePlayerBM,
                main_prompt_header=ACCUSE_MAIN_HEADER,
                temperature=0.5
            ),
            "joke": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=JOKE_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=JokeBM,
                main_prompt_header=JOKE_MAIN_HEADER,
                temperature=0.5
            ),
            "question": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=QUESTION_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=QuestionBM,
                main_prompt_header=QUESTION_MAIN_HEADER,
                temperature=0.5
            ),
            "simple_phrase": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=SIMPLE_PHRASE_EXAMPLES,
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=SimplePhraseBM,
                main_prompt_header=SIMPLE_PHRASE_MAIN_HEADER,
                temperature=0.5
            ),
            "other": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=OTHER_EXAMPLES,  # Reusing simple phrase examples for fallback
                prompt_headers=GENERIC_PROMPT_HEADERS,
                output_format=SimplePhraseBM,
                main_prompt_header=OTHER_MAIN_HEADER,
                temperature=0.5
            ),
             #  Game summary update prompter
            "game_summary_update": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=GSU_EXAMPLES,
                prompt_headers=GSU_HEADERS,
                output_format=GameSummaryBM,
                main_prompt_header=GSU_MAIN_HEADER
            )
        }
            
    def _initialize_game_summary(self) -> str:
        """Initializes the game summary for the AI player."""
        self.game_summary = GameSummaryBM(
            round_number=0,
            players_alive=self.players_code_names,
            players_voted_off=[],
            last_vote_outcome="N/A",
            textual_summary="The game has started. Players are introducing themselves."
        ).model_dump_json()
        return self.game_summary

    def _steal_player_state(self, player_state_to_steal: PlayerState) -> PlayerState:
        """Creates a modified copy of the human persona instead of modifying the original."""
        color_name = color_name=SequentialAssigner(COLORS_PATH, COLORS_INDEX_PATH).assign()
        player_state = PlayerState(
            first_name=player_state_to_steal.first_name,
            last_initial=player_state_to_steal.last_initial,
            grade=player_state_to_steal.grade,
            lobby_id=player_state_to_steal.lobby_id,
            favorite_food=player_state_to_steal.favorite_food,
            favorite_animal=player_state_to_steal.favorite_animal,
            hobby=player_state_to_steal.hobby,
            extra_info=player_state_to_steal.extra_info,
            color_name=color_name,
            color=COLOR_DICT[color_name],
            code_name=SequentialAssigner(NAMES_PATH, NAMES_INDEX_PATH).assign()
        )
        self.logger = StandAloneLogger(
            log_path=f"./logs/ai_{player_state.code_name}.log",
            clear=True,
            init=True
        )
        self.logger.info(f"Stolen player_state: {player_state}")
        return player_state
    
    def _update_player_minutes(self, minutes: List[str]):
        """Updates the player minutes with the latest game messages."""
        if len(minutes) > 0 and minutes[-1].startswith(f"{self.origin_code_name}:"):
            last_message = minutes[-1].split(": ", 1)[1]  # Extract the message after the player name
            self.player_minutes.append(last_message)

    def _stylize_output(self, before_styling: str) -> str:
        """Stylizes the output to better match the human player."""
        response_json = self.prompter_dict["stylizer"].get_completion({
            "input_text": before_styling,
            "player_minutes": self.player_minutes
        })
        self.logger.info(f"Stylized JSON: {response_json}")
        stylized_response = StylizerBM.model_validate_json(json.dumps(response_json)).output_text
        return stylized_response

    def decide_to_respond(self, minutes: List[str]):
        print("--- decide_to_respond ---")
        """Determines whether AI should respond and what action to take."""

        self._update_player_minutes(minutes)

        if not minutes:
            return "Wait for next message"

        try:
            response_json = self.prompter_dict["decide_to_respond"].get_completion({
                "minutes": minutes,
                "game_summary": self.game_summary
            })
            self.logger.info(f"DTR JSON: {response_json}")
            decision = DecideToRespondBM.model_validate_json(json.dumps(response_json))
        except Exception as e:
            if self.debug_bool:
                raise
            self.logger.error(f"decide_to_respond – LLM Response: {locals().get('response_json')}")
            self.logger.error(f"decide_to_respond – Error: {e}")
            return "I'm thinking... let's wait and see what happens next."

        if not self.has_introduced and decision.havent_indroduced_self:
            self.has_introduced = True
            return self.introduce(minutes)

        if decision.directed_at_me or decision.accused:
            return self.choose_action(minutes)

        return "Wait for next message"


    def choose_action(self, minutes: List[str]):
        print("--- CHOOSE ACTION ---")
        try:
            response_json = self.prompter_dict["choose_action"].get_completion({
                "minutes": minutes,
                "game_summary": self.game_summary
            })
            self.logger.info(f"Action Choice JSON: {response_json}")
            action = ActionOptionBM.model_validate_json(json.dumps(response_json))
        except Exception as e:
            if self.debug_bool:
                raise
            self.logger.error(f"choose_action – LLM Response: {locals().get('response_json')}")
            self.logger.error(f"choose_action – Error: {e}")
            return "Sorry, I got confused about what to say next."

        if action.defend:
            return self.defend(minutes)
        elif action.accuse:
            return self.accuse(minutes)
        elif action.joke:
            return self.joke(minutes)
        elif action.question:
            return self.question(minutes)
        else:
            return self.other(minutes)


    @handle_errors()
    def introduce(self, minutes: List[str]):
        """Introduces the AI player to the game."""
        print("--- INTRODUCE ---")
        response_json = self.prompter_dict["introduce"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Introduce JSON: {response_json}")
        # print("INTRO RESPONSE:", response_json)
        self.has_introduced = True
        # print(type(response_json))
        output = IntroBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def defend(self, minutes: List[str]):
        print("--- DEFEND ---")
        """Defends the AI player from accusations."""
        response_json = self.prompter_dict["defend"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Defend JSON: {response_json}")
        output =  DefendYourselfBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def accuse(self, minutes: List[str]):
        """Accuses another player of being a robot."""
        print("--- ACCUSE ---")
        response_json = self.prompter_dict["accuse"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Accuse JSON: {response_json}")
        output = AccusePlayerBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def joke(self, minutes: List[str]):
        """Tells a joke to lighten the mood."""
        print("--- JOKE ---")
        response_json = self.prompter_dict["joke"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Joke JSON: {response_json}")
        output = JokeBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def question(self, minutes: List[str]):
        """Asks another player a question."""
        print("--- QUESTION ---")
        response_json = self.prompter_dict["question"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Question JSON: {response_json}")
        output = QuestionBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def simple_phrase(self, minutes: List[str]):
        """Says a simple phrase to keep the conversation going."""
        print("--- SIMPLE PHRASE ---")
        response_json = self.prompter_dict["simple_phrase"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Simple Phrase JSON: {response_json}")
        output = SimplePhraseBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def other(self, minutes: List[str]):
        """Handles any other action that doesn't fit the predefined categories."""
        print("--- OTHER ---")
        response_json = self.prompter_dict["other"].get_completion({
            "minutes": minutes,
            "game_summary": self.game_summary
        })
        self.logger.info(f"Other JSON: {response_json}")
        output = SimplePhraseBM.model_validate_json(json.dumps(response_json)).output_text
        stylized_output = self._stylize_output(output)
        return stylized_output
    
    @handle_errors()
    def game_summary_update(self, minutes: List[str], vote_result: dict, game_summary):
        """Updates the game state based on vote results and discussion."""
        print("--- GAME SUMMARY UPDATE ---")
        response_json = self.prompter_dict["game_summary_update"].get_completion({
            "minutes": "\n".join(minutes),
            "game_summary": json.loads(game_summary.model_dump_json()),  #  Convert JSON string back into dict
            "vote_result": vote_result  # Already a dict, no need to modify
        })
        self.logger.info(f"Game Summary Update JSON: {response_json}")
        updated_game_summary = GameSummaryBM.model_validate_json(json.dumps(response_json))
        self.game_summary = json.loads(updated_game_summary.model_dump_json())

    