from colorama import Fore, Style
from utils.states import ScreenState, PlayerState, GameState
from utils.asthetics import clear_screen

def score_screen(
        ss: ScreenState, ps: PlayerState, gs: GameState
    ) -> tuple[ScreenState, PlayerState, GameState]:
    """
    Displays the game results and final scores.
    """
    clear_screen()
    print(Fore.YELLOW + "=== FINAL SCOREBOARD ===\n" + Style.RESET_ALL)

    # Sort players alphabetically
    all_players = sorted(gs.players + gs.players_voted_off, key=lambda p: p.code_name)

    print(Fore.CYAN + "Players and Teams:" + Style.RESET_ALL)
    for player in all_players:
        team = "Human" if player.is_human else "Bot"
        status = "✓" if player.still_in_game else "❌"
        print(f"{status} {player.code_name} ({team}) - {player.color_name}")

    print("\n" + Fore.CYAN + "Final Scores:" + Style.RESET_ALL)
    for player in all_players:
        score = getattr(player, "score", "N/A")  # If score isn't tracked yet, display N/A
        print(f"{player.code_name}: {score}")

    print("\n" + Fore.CYAN + "Voting Summary:" + Style.RESET_ALL)
    total_ai = len([p for p in all_players if not p.is_human])
    voted_out_ai = len([p for p in gs.players_voted_off if not p.is_human])
    print(f"Bots voted out: {voted_out_ai} / {total_ai}")

    print("\n" + Fore.CYAN + "💡 Prompt Engineering Insight:" + Style.RESET_ALL)
    print("The AI bots crafted responses using the personal info you shared.")
    print("Pay attention to how your hobbies, favorite foods, and fun facts were used to mimic human behavior.")
    print("Were any bots able to fool you? 👀")

    print()
    input(Fore.MAGENTA + "Press Enter to return to the intro screen..." + Style.RESET_ALL)

    return ScreenState.INTRO, ps, gs