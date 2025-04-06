from colorama import Fore, Style
from utils.asthetics import format_gm_message
from utils.states import GameState, PlayerState, ScreenState

def play_game(ss: ScreenState, gs: GameState, ps: PlayerState
              ) -> tuple[ScreenState, GameState, PlayerState]:
    """Main game loop for the chat phase (placeholder for debugging voting logic)."""
    print(format_gm_message('-------------- FAKE CHAT PHASE --------------'))
    print(f"YOU ARE PLAYING AS {ps.code_name}.\n")
    print(f"REMAINING PLAYERS:")
    for player in gs.players:
        print(f"{player.code_name} (Human?: {'yes' if player.is_human else 'no'} - {'in' if player.still_in_game else 'out'})")
    print("\n------------------------------\n")

    # Wait for user input to proceed to the voting phase
    input(Fore.MAGENTA + "\nPress Enter to continue to the voting phase..." + Style.RESET_ALL)

    # Transition to voting state
    ss = ScreenState.VOTE
    return ss, gs, ps
