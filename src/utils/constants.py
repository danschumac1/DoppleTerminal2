from utils.states import GameState, PlayerState

ROUND_DURATION = 60  # seconds

# COLOR_DICT = {
#     "RED": "\x1b[31m",
#     "GREEN": "\x1b[32m",
#     "YELLOW": "\x1b[33m",
#     "BLUE": "\x1b[34m",
#     "MAGENTA": "\x1b[35m",
#     "CYAN": "\x1b[36m",
#     "WHITE": "\x1b[0m"
# }

NAMES_PATH="./data/runtime/possible_code_names.json"
NAMES_INDEX_PATH="./data/runtime/code_names_index.txt"
# COLORS_PATH="./data/runtime/possible_colors.json"
# COLORS_INDEX_PATH="./data/runtime/colors_index.txt"

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
    # color_name="",
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