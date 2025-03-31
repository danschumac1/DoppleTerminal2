from utils.states import ScreenState, PlayerState, GameState

def score_screen(
        ss: ScreenState, ps: PlayerState, gs: GameState) -> tuple[ScreenState, PlayerState, GameState]:
    """
    Displays the game results and final scores.
    """
    print("=== SCORE SCREEN ===")
    print("TODO: Display game results and final scores")
    input("Press Enter to continue...")
    return ScreenState.INTRO, ps, gs