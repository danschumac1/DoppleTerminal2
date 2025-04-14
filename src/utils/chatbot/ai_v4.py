import asyncio
from dataclasses import asdict
import json
from typing import List 
from pydantic import BaseModel
from .prompter import OpenAIPrompter, QAs
from . import examples_v4 as ex4
from . import enums_dcs_v3 as dcs3
import sys

from utils.chatbot import prompter
sys.path.append("../../")
from utils.states import PlayerState, GameState
from utils.file_io import SequentialAssigner
from utils.constants import (
    NAMES_PATH, NAMES_INDEX_PATH, 
    COLORS_PATH, COLORS_INDEX_PATH
    )
from utils.logging_utils import StandAloneLogger

class AIPlayer:
    def __init__(
            self,
            player_to_steal: PlayerState, 
            system_prompt: str = ex4.DEFAULT_SYSTEM_PROMPT,
            debug_bool: bool = False):
        self.humans_messages = []
        self.stolen_player_code_name = player_to_steal.code_name
        self.code_name_assigner = SequentialAssigner(NAMES_PATH, NAMES_INDEX_PATH, "code_names")
        self.color_assigner = SequentialAssigner(COLORS_PATH, COLORS_INDEX_PATH, "colors")
        self.player_state = self._steal_player_state(player_to_steal)
        self.system_prompt = system_prompt + json.dumps(asdict(self.player_state))
        self.is_voted_out = False

        self.debug_bool = debug_bool

        # Initialize game state
        self.game_state = None
        self.logger = self._init_logger()
        
        # Prompter Dictionary : Updated Prompter Dictionary with prompt_headers
        # Initialize custom prompter_dict
        self.prompter_dict = {
            "decide_to_respond": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.DTR_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.DecideToRespondBM,
                main_prompt_header=self._update_main_header(ex4.DTR_MAIN_HEADER),
            ),
            "choose_action": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.CHOSE_ACTION_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=ex4.ActionOptionBM,
                main_prompt_header=self._update_main_header(ex4.CHOOSE_ACTION_MAIN_HEADER)
            ),
            "introduce": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.INTRO_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.IntroBM,
                main_prompt_header=self._update_main_header(ex4.INTRO_MAIN_HEADER),
                temperature=0.5
            ),
            "defend": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.DEFEND_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.DefendYourselfBM,
                main_prompt_header=self._update_main_header(ex4.DEFEND_MAIN_HEADER),
                temperature=0.5
            ),
            "accuse": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.ACCUSE_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.AccusePlayerBM,
                main_prompt_header=self._update_main_header(ex4.ACCUSE_MAIN_HEADER),
                temperature=0.5
            ),
            "joke": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.JOKE_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.JokeBM,
                main_prompt_header=self._update_main_header(ex4.JOKE_MAIN_HEADER,),
                temperature=0.5
            ),
            "question": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.QUESTION_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.QuestionBM,
                main_prompt_header=self._update_main_header(ex4.QUESTION_MAIN_HEADER,),
                temperature=0.5
            ),
            "simple_phrase": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.SIMPLE_PHRASE_EXAMPLES,
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.SimplePhraseBM,
                main_prompt_header=self._update_main_header(ex4.SIMPLE_PHRASE_MAIN_HEADER,),
                temperature=0.5
            ),
            "other": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.OTHER_EXAMPLES,  # Reusing simple phrase examples for fallback
                prompt_headers=ex4.GENERIC_PROMPT_HEADERS,
                output_format=dcs3.SimplePhraseBM,
                main_prompt_header=self._update_main_header(ex4.OTHER_MAIN_HEADER),
                temperature=0.5
            ),
              "stylizer": OpenAIPrompter(
                openai_dict_key="OPENAI_API_KEY",
                system_prompt=self.system_prompt,
                examples=ex4.STYLIZE_EXAMPLES,
                prompt_headers=ex4.STYLIZE_HEADERS,
                output_format=dcs3.StylizerBM,
                main_prompt_header=self._update_main_header(ex4.STYLIZE_MAIN_HEADER),
            )
        }

    def _update_main_header(self, main_header: str) -> str:
        """Replace placeholders in the main header with player-specific values."""
        # Get the persona dictionary and format it as a string
        persona_str = json.dumps(self.player_state.to_persona(), ensure_ascii=False)
        return main_header.replace(
            "NAME", f"{self.player_state.first_name} {self.player_state.last_initial}"
        ).replace(
            "CODE_NAME", f"{self.player_state.code_name}"
        ).replace(
            "PERSONA", persona_str
        )

    def _update_examples(self, examples: List[QAs]) -> List[QAs]:
        """Update examples with the player's name, code name, and persona."""
        # Get the persona dictionary and format it as a string
        persona_str = json.dumps(self.player_state.to_persona(), ensure_ascii=False)
        for example in examples:
            # Iterate over each key-value pair in the example's question dictionary
            for key, value in example.question.items():
                # Check if the value is a string (as it might be JSON or formatted text)
                if isinstance(value, str):
                    # Replace placeholders within the string value
                    value = value.replace(
                        "NAME", f"{self.player_state.first_name} {self.player_state.last_initial}"
                    ).replace(
                        "CODE_NAME", f"{self.player_state.code_name}"
                    ).replace(
                        "PERSONA", persona_str
                    )
                    # Update the example with the modified string
                    example.question[key] = value
                elif isinstance(value, list):
                    # If the value is a list of strings (like minutes), update each string
                    updated_list = [
                        line.replace(
                            "NAME", f"{self.player_state.first_name} {self.player_state.last_initial}"
                        ).replace(
                            "CODE_NAME", f"{self.player_state.code_name}"
                        ).replace(
                            "PERSONA", persona_str
                        )
                        for line in value
                    ]
                    example.question[key] = updated_list
            # Log the updated example for debugging
            self.logger.info(f"Updated example: {example}")
        return examples
    
    # @handle_errors()
    async def decide_to_respond(self, minutes: List[str], chat_log: str) -> str:
        """Step 1: Decide whether the AI should respond."""
        prompter = self.prompter_dict["decide_to_respond"]
        input_texts = {
            "minutes": "\n".join(minutes),
            # "game_state": json.dumps(self.game_state.to_dict())
        }
        # self.logger.info(f"DTR PROMPT: {prompter.fetch_prompt(input_texts)}")

        last_msg = minutes[-1] if minutes else None
        if last_msg and last_msg.startswith(f"{self.stolen_player_code_name}:"):
            self.humans_messages.append(last_msg.split(":", 1)[1].strip())

        try:
            response_json = await asyncio.to_thread(prompter.get_completion, input_texts)
        except Exception as e:
            self.logger.error(f"Error during decision to respond: {e}")
            return "Error during decision making."

        self.logger.info(f"DTR JSON: {response_json}")
        decision = dcs3.DecideToRespondBM.model_validate_json(json.dumps(response_json))


        if decision.respond_bool:
            return await self.choose_action(minutes, chat_log)
        return "No response needed."


    async def choose_action(self, minutes: List[str], chat_log: str) -> str:
        """Step 2: Choose the appropriate action if AI should respond."""
        prompter = self.prompter_dict["choose_action"]
        input_texts = {
            "minutes": "\n".join(minutes),
            # "game_state": json.dumps(self.game_state.to_dict())
        }
        # self.logger.info(f"CHOOSE ACTION PROMPT: {prompter.fetch_prompt(input_texts)}")

        try:
            response_json = await asyncio.to_thread(prompter.get_completion, input_texts)
        except Exception as e:
            self.logger.error(f"Error during choosing action: {e}")
            return "Error during choosing action."

        self.logger.info(f"Choose Action JSON: {response_json}")
        action = dcs3.ActionOptionBM.model_validate_json(json.dumps(response_json))
        self.logger.info(f"Action chosen: {action}")

        if action.introduce:
            return await self.generate_action_response(
                "introduce", minutes, chat_log, dcs3.IntroBM)
        elif action.defend:
            return await self.generate_action_response(
                "defend", minutes, chat_log, dcs3.DefendYourselfBM)
        elif action.accuse:
            return await self.generate_action_response(
                "accuse", minutes, chat_log, dcs3.AccusePlayerBM)
        elif action.joke:
            return await self.generate_action_response(
                "joke", minutes, chat_log, dcs3.JokeBM)
        elif action.question:
            return await self.generate_action_response(
                "question", minutes, chat_log, dcs3.QuestionBM)
        elif action.simple_phrase:
            return await self.generate_action_response(
                "simple_phrase", minutes, chat_log, dcs3.SimplePhraseBM)
        elif action.other:
            return await self.generate_action_response(
                "other", minutes, chat_log, dcs3.OtherBM)
        else:
            self.logger.error("Unknown action type chosen.")
            return "Error: Unknown action type."


    async def generate_action_response(
            self, action_type: str, minutes: List[str], chat_log: str, validator:BaseModel) -> str:
        """Step 3: Generate the response based on the chosen action type."""
        prompter = self.prompter_dict[action_type]
        input_texts = {
            "minutes": "\n".join(minutes),
            # "game_state": json.dumps(self.game_state.to_dict())
        }
        # print(f"{action_type.upper()} RESPONSE: {prompter.fetch_prompt(input_texts)}")

        try:
            response_json = await asyncio.to_thread(prompter.get_completion, input_texts)
        except Exception as e:
            self.logger.error(f"Error during {action_type} response generation: {e}")
            return f"Error during {action_type} response generation."

        # self.logger.info(f"{action_type.capitalize()} Response JSON: {response_json}")
        resp_text = validator.model_validate_json(json.dumps(response_json))

        self.logger.info(f"{action_type.capitalize()} Initial Response: {resp_text}")
        return await self.stylize_response(resp_text, chat_log)


    async def stylize_response(self, response: str, chat_log: str) -> str:
        """Step 4: Stylize the generated response."""
        prompter = self.prompter_dict["stylizer"]
        input_texts = {
            "response": response,
            "examples": "\n".join(self.humans_messages)
        }

        try:
            response_json = await asyncio.to_thread(prompter.get_completion, input_texts)
            styled_response = dcs3.StylizerBM.model_validate_json(json.dumps(response_json)).output_text
            self.logger.info(f"Stylized Response: {styled_response}")
            return styled_response
        except Exception as e:
            self.logger.error(f"Error during stylizing response: {e}")
            return "I think that too"  # Fallback response
    
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
            log_path=f"./data/runtime/lobbies/lobby_{self.player_state.lobby_id}/ai/{self.player_state.code_name}.log",
            clear=True,
            init=True
        )
        return logger
    
    def initialize_game_state(self, game_state: GameState):
        """Initialize the game state."""
        self.game_state = game_state
        self.logger.info(f"Game state initialized with players: {self.stolen_player_code_name}")
        self.logger.info(f"Game state: {self.game_state.to_dict()}")