from colorama import Fore, init

from utils.states import GameState, PlayerState

ROUND_DURATION = 6  # seconds

COLOR_DICT = {
    "RED": Fore.RED,
    "GREEN": Fore.GREEN,
    "YELLOW": Fore.YELLOW,
    "BLUE": Fore.BLUE,
    "MAGENTA": Fore.MAGENTA,
    "CYAN": Fore.CYAN,
}

NAMES_PATH="./data/runtime/possible_code_names.json"
NAMES_INDEX_PATH="./data/runtime/code_names_index.txt"
COLORS_PATH="./data/runtime/possible_colors.json"
COLORS_INDEX_PATH="./data/runtime/colors_index.txt"

BLANK_PS = PlayerState(
    lobby_id="",
    first_name="",
    last_initial="",
    code_name="",
    grade="",
    favorite_food="",
    favorite_animal="",
    hobby="",
    extra_info="",
    is_human=True,  
    color_name="",
    # color_asci=""
)

BLANK_GS = GameState(
    round_number=0,
    players=[],
    players_voted_off=[],
    last_vote_outcome="",
)

ICEBREAKERS = [
    ""
]