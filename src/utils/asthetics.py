import os
# from prompt_toolkit.formatted_text import ANSI
# from prompt_toolkit.shortcuts import print_formatted_text
# from utils.constants import COLOR_DICT
from utils.states import GameState

# def get_color_for_code_name(code_name: str, gs: GameState) -> str:
#     for player in gs.players:
#         if player.code_name == code_name:
#             return player.color_name
#     raise ValueError(f"Unknown code_name in chat: '{code_name}'")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# def print_color(text: str, color: str, print_or_return="print") -> None:
#     """
#     Print text in a specific color using ANSI escape codes.
#     """
#     # ensure print_or_return is either "print" or "return"
#     if print_or_return not in ["print", "return"]:
#         raise ValueError("print_or_return must be either 'print' or 'return'")
#     if color not in COLOR_DICT and color != "WHITE":
#         raise ValueError(
#             f"Invalid color: {color}. Available colors are: {', '.join(COLOR_DICT.keys())}")
#     if color == "WHITE":
#         ansi_text = "\x1b[0m" + text
#     else:
#         ansi_text = f"{COLOR_DICT[color]}{text}\x1b[0m"
#     if print_or_return == "print":
#         print_formatted_text(ANSI(ansi_text))
#     else:
#         return ansi_text
    
def format_gm_message(msg: str) -> str:
    # top = print_color("*" * 50, "YELLOW", print_or_return="return")
    # mid = print_color(f"GAME MASTER: {msg}", "YELLOW", print_or_return="return")
    # bot = print_color("*" * 50, "YELLOW", print_or_return="return")
    top = "*" * 50
    mid = f"GAME MASTER: {msg}"
    bot = "*" * 50
    return f"{top}\n{mid}\n{bot}"

# def get_color_for_code_name(code_name: str, gs: GameState) -> str:
#     for player in gs.players:
#         if player.code_name == code_name:
#             return player.color_name
#     return "WHITE"