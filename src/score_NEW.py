from colorama import Fore, Style
from utils.states import ScreenState, PlayerState, GameState
from utils.asthetics import clear_screen

def score_screen(
        ss: ScreenState, gs: GameState, ps: PlayerState
    ) -> tuple[ScreenState, GameState, PlayerState]:
    """
    Displays the game results and final scores with detailed statistics.
    """
    clear_screen()
    print(Fore.YELLOW + "=== 🏆 FINAL SCOREBOARD 🏆 ===\n" + Style.RESET_ALL)

    # Combine active and voted off players
    all_players = gs.players + gs.players_voted_off
    
    # Sort all players by code name
    all_players = sorted(all_players, key=lambda p: p.code_name)

    # Display Players and Teams with enhanced formatting
    print(Fore.CYAN + "👥 Players and Teams:" + Style.RESET_ALL)
    print("─" * 50)
    for player in all_players:
        team = "👤 Human" if player.is_human else "🤖 Bot"
        status = "✅ Active" if player.still_in_game else "❌ Voted Out"
        print(f"{player.code_name:<15} | {team:<10} | {status:<12} | {player.color_name}")
    print("─" * 50 + "\n")

    # Display Game Statistics
    print(Fore.CYAN + "📊 Game Statistics:" + Style.RESET_ALL)
    print("─" * 50)
    
    # Calculate statistics
    total_players = len(all_players)
    total_humans = len([p for p in all_players if p.is_human])
    total_bots = len([p for p in all_players if not p.is_human])
    voted_out_humans = len([p for p in gs.players_voted_off if p.is_human])
    voted_out_bots = len([p for p in gs.players_voted_off if not p.is_human])
    
    print(f"Total Rounds Played: {gs.round_number}")
    print(f"Total Players: {total_players} ({total_humans} humans, {total_bots} bots)")
    print(f"Players Voted Out: {len(gs.players_voted_off)} ({voted_out_humans} humans, {voted_out_bots} bots)")
    
    # Calculate success rates
    bot_detection_rate = (voted_out_bots / total_bots * 100) if total_bots > 0 else 0
    print(f"Bot Detection Rate: {bot_detection_rate:.1f}%")
    print("─" * 50 + "\n")

    # Display Final Game Outcome
    print(Fore.CYAN + "🎯 Game Outcome:" + Style.RESET_ALL)
    print("─" * 50)
    if bot_detection_rate >= 50:
        print(Fore.GREEN + "🎉 Humans win! Successfully identified majority of bots!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "😔 Bots win! Less than 50% of bots were detected." + Style.RESET_ALL)
    print("─" * 50 + "\n")

    # Display Prompt Engineering Insight
    print(Fore.CYAN + "💡 Prompt Engineering Insight:" + Style.RESET_ALL)
    print("─" * 50)
    print("The AI bots used these strategies to mimic human behavior:")
    print("• Incorporated personal info from player profiles")
    print("• Generated contextually relevant responses")
    print("• Maintained consistent personality traits")
    print("• Used natural language patterns and casual chat style")
    print("─" * 50)

    print()
    input(Fore.MAGENTA + "Press Enter to return to the intro screen..." + Style.RESET_ALL)

    return ScreenState.INTRO, gs, ps