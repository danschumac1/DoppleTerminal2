from datetime import datetime
import os
from typing import Tuple

from colorama import Fore, Style
from utils.chatbot.ai import AIPlayer
from utils.logging_utils import MasterLogger, StandAloneLogger
from utils.states import GameState, ScreenState, PlayerState
from utils.file_io import SequentialAssigner, init_game_file, load_players_from_lobby, save_player_to_lobby_file
from utils.constants import (
    COLORS_INDEX_PATH, COLORS_PATH, NAMES_PATH, NAMES_INDEX_PATH, 
    # COLORS_PATH, COLORS_INDEX_PATH, COLOR_DICT
)
from utils.asthetics import clear_screen # ,print_color
from datetime import datetime # , timedelta
from time import sleep

class PlayerSetup:
    """
    Handles the player setup process, including collecting player information,
    assigning a code name and color, and creating a PlayerState object.
    """

    def __init__(
        self,
        names_path=NAMES_PATH,
        names_index_path=NAMES_INDEX_PATH,
        colors_path=COLORS_PATH,
        colors_index_path=COLORS_INDEX_PATH
    ):
        """
        Initializes the PlayerSetup object with necessary paths for name and color assignment.

        Args:
            names_path (str): Path to the file containing player names.
            names_index_path (str): Path to the file tracking the current name index.
            colors_path (str): Path to the file containing color names.
            colors_index_path (str): Path to the file tracking the current color index.
        """
        self.data = {}
        self.code_name_assigner = SequentialAssigner(names_path, names_index_path, "code_names")
        self.color_assigner = SequentialAssigner(colors_path, colors_index_path, "colors")


    def prompt_input(self, field_name: str, prompt: str) -> None:
        """Prompt for a generic input and ensure it is not empty."""
        while True:
            value = input(Fore.CYAN + prompt + " " + Style.RESET_ALL).strip()
            if value:
                self.data[field_name] = value
                return
            # print_color(f"{field_name} cannot be empty.", "RED")
            print(Fore.RED + f"{field_name} cannot be empty." + Style.RESET_ALL)

    def prompt_number(self, lower: int, upper: int, prompt: str, field_name: str) -> None:
        while True:
            try:
                value = int(input(Fore.CYAN + f"{prompt} ({lower} - {upper}): " + Style.RESET_ALL))
                if lower <= value <= upper:
                    self.data[field_name] = value
                    return
                print(Fore.RED + f"Please enter a number between {lower} and {upper}." + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Invalid input. Please enter a valid number." + Style.RESET_ALL)

    def prompt_initial(self) -> None:
        while True:
            value = input(Fore.CYAN + "Enter your last initial (A–Z): " + Style.RESET_ALL).strip().upper()
            if len(value) == 1 and value.isalpha():
                self.data["last_initial"] = value
                return
            print(Fore.RED + "Invalid input. Please enter a single letter (A–Z)." + Style.RESET_ALL)

    def run(self, gs:GameState) -> Tuple[ScreenState, GameState, PlayerState]:
        """Run the player setup process."""
        # picked_color_name = self.assign_color()
        # self.data["color_name"] = picked_color_name
        # self.data["color_asci"] = COLOR_DICT[picked_color_name]
        
        # print_color("=== Player Setup ===", "CYAN")
        print(Fore.YELLOW + "\n=== Player Setup ===" + Style.RESET_ALL)
        self.prompt_number(1, 10000, "Enter your lobby number", "lobby")
        self.prompt_number(1, 5, "How many people are you playing with?", "number_of_human_players") # TODO change back to 3,5
        self.prompt_number(6, 8, "What grade are you in?", "grade")
        self.prompt_input("first_name", "Enter your first name: ")
        self.prompt_initial()
        self.prompt_input("favorite_food", "Favorite food: ")
        self.prompt_input("favorite_animal", "Favorite animal: ")
        self.prompt_input("hobby", "What's your hobby? ")
        self.prompt_input("extra_info", "Tell us one more thing about you: ")

        print(Fore.GREEN + "✅ Player setup complete." + Style.RESET_ALL)

        lobby_path = os.path.join(
            "data", "runtime", "lobbies",
            f"lobby_{self.data['lobby']}"
        )
        gs.chat_log_path = os.path.join(lobby_path, "chat_log.txt")
        gs.start_time_path = os.path.join(lobby_path, "starttime.txt")
        gs.voting_path = os.path.join(lobby_path, "voting.json")
        gs.player_path = os.path.join(lobby_path, "players.json")
        gs.number_of_human_players = self.data["number_of_human_players"]

        # Create the PlayerState object
        code_name = self.code_name_assigner.assign()
        color_name = self.color_assigner.assign()
        ps = PlayerState(
            lobby_id=self.data["lobby"],
            first_name=self.data["first_name"],
            last_initial=self.data["last_initial"],
            grade=self.data["grade"],
            code_name=code_name,
            favorite_food=self.data["favorite_food"],
            favorite_animal=self.data["favorite_animal"],
            hobby=self.data["hobby"],
            extra_info=self.data["extra_info"],
            is_human=True,
            color_name=color_name,
        )
        save_player_to_lobby_file(ps)
        ps.logger = StandAloneLogger(
            log_path=f"./data/runtime/lobbies/lobby_{ps.lobby_id}/{ps.first_name}{ps.last_initial}{ps.grade}_game_log.log",
            clear=True,
            init=True
        )
        # ps.logger.info(f"Player {ps.code_name} initialized with color: {picked_color_name}")

        # NEEDS TO GO LAST
        ps.ai_doppleganger = AIPlayer(
            player_to_steal=ps
        )
        return ps, gs, ps

def collect_player_data(
        ss: ScreenState,
        gs: GameState,
        ps: PlayerState,
    ) -> Tuple[ScreenState, GameState, PlayerState]:

    print_str = ''
    master_logger = MasterLogger.get_instance()

    # Setup player data if not already written
    if not any(p == ps.code_name for p in gs.players):
        master_logger.log("Starting Setup screen...")
        ps.written_to_file = True
        player_setup = PlayerSetup()
        ps, gs, ps = player_setup.run(gs)  # Corrected the call to run method
        gs.players.append(ps)
        gs.players.append(ps.ai_doppleganger.player_state)
        save_player_to_lobby_file(ps.ai_doppleganger.player_state)

    # Initialize chat file if not present
    if not os.path.exists(gs.chat_log_path):
        init_game_file(gs.chat_log_path)
        master_logger.log(f"Initialized chat log at {gs.chat_log_path}")
    # Initialize voting file if not present
    if not os.path.exists(gs.voting_path):
        init_game_file(gs.voting_path)
        master_logger.log(f"Initialized voting file at {gs.voting_path}")

    # master_logger.log(
    #     f"Color selected for AI Player {ps.ai_doppleganger.player_state.code_name}: {ps.ai_doppleganger.player_state.color_name}")
    master_logger.log(f"Created AI doppelganger for {ps.first_name} {ps.last_initial}")

    # Check the number of human players and start the game if ready
    while len(gs.players) < gs.number_of_human_players:
        # every 1 second check the file
        sleep(1)
        # Load the current players from the lobby file
        gs.players = load_players_from_lobby(gs)

        # Filter out AI doppelgangers to count human players only
        human_players = [p for p in gs.players if not p.ai_doppleganger]
        new_str = f"{len(human_players)}/{gs.number_of_human_players} players are ready."
        if print_str != new_str:
            # print_color(new_str, "YELLOW")
            print(new_str)
            print_str = new_str

    # All players are ready, continue to the next step
    input(Fore.MAGENTA + "Press Enter to continue..." + Style.RESET_ALL)
    # clear_screen() # TODO uncomment this line to clear the screen

    # Synchronize start time if this player is the timekeeper
    if not os.path.exists(gs.start_time_path):
        gs.players = load_players_from_lobby(gs)
        # print("GS.PLAYERS: ", gs.players)
        # Assign the current player as the timekeeper
        ps.timekeeper = True
        master_logger.log(f"Player {ps.code_name} is the timekeeper.")
        # Create the start time file
        init_game_file(gs.start_time_path)
        # Write the start time to the file
        ps.starttime = datetime.now().replace(tzinfo=None)
        start_time_str = ps.starttime.strftime("%Y-%m-%d %H:%M:%S")
        with open(gs.start_time_path, "w") as f:
            f.write(start_time_str)
        # Log the start time
        master_logger.log(f"Initialized start time at {gs.start_time_path}")
    else:
        # If not the timekeeper, wait for the file to exist
        while not os.path.exists(gs.start_time_path):
            print("Waiting for the timekeeper to initialize the start time...")
            sleep(1)

        # Load the starting time
        with open(gs.start_time_path, "r") as f:
            start_time_str = f.read().strip()
            ps.starttime = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            ps.starttime = ps.starttime.replace(tzinfo=None)  # Remove timezone info
        master_logger.log(f"Loaded existing start time: {ps.starttime}")

    # Finally, initialize the game state for the AI doppelganger

    ps.ai_doppleganger.initialize_game_state(gs)
    all_players = load_players_from_lobby(gs)
    # Update the AI doppelganger's player code names
    ps.ai_doppleganger.players_code_names = [p.code_name for p in all_players]

    return ScreenState.CHAT, gs, ps
