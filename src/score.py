from utils.states import ScreenState, PlayerState, GameState

def score_screen(
        ss: ScreenState, ps: PlayerState, gs: GameState) -> tuple[ScreenState, PlayerState, GameState]:
    """
    Displays the game results and final scores.
    """
    print("=== SCORE SCREEN ===")
    print("TODO: Display game results and final scores")
    ##  TODO:
    #   - List players and their team (human or bot)
    #   - List each player's score
    #   - List voting results? Or how many bots were voted out
    #   - Info on prompt engineering and how their info was used against them
    print()
    input("Press Enter to continue...")
    return ScreenState.INTRO, ps, gs