from colorama import Fore, init

from utils.states import GameState, PlayerState

ROUND_DURATION = 30  # seconds

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
    "Welcome to the game! Everyone please introduce yourself using your first name and last initial.",
    "If you could have any superpower, what would it be and why?",
    "If you could travel anywhere in the world, where would you go and why?",
    "What is your favorite book or movie, and why do you love it?",
    "If you could have dinner with any historical figure, who would it be and why?",
    "What is your favorite childhood memory?",
    "If you could instantly learn any skill, what would it be and why?",
    "What is your dream job, and why?",
    "If you could time travel to any period in history, when would it be and why?",
    "What is your favorite hobby or pastime?",
    "If you could meet any fictional character, who would it be and why?",
]