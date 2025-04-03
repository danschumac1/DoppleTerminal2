from utils.states import GameState, PlayerState, ScreenState

def play_game(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    """Main game loop for the chat phase (placeholder for debugging voting logic)."""
    print("=== Chat Phase (Debug Placeholder) ===")
    print(f"Player {ps.code_name} has entered the chat.")
    print("Simulating some chat messages:")
    
    # Simulated chat messages
    dummy_messages = [
        f"{ps.code_name}: Hey everyone, what are we thinking?",
        "PLAYER_A: I have a suspicion about PLAYER_B.",
        "PLAYER_B: Why are you accusing me?",
        f"{ps.code_name}: Just thinking out loud...",
        "GAME MASTER: 30 seconds left!"
    ]

    # Print each dummy message
    for message in dummy_messages:
        print(message)

    # Wait for user input to proceed to the voting phase
    input("\nPress Enter to continue to the voting phase...")

    # Transition to voting state
    ss = ScreenState.VOTE
    print("Transitioning to voting phase...\n")
    return ss, gs, ps
