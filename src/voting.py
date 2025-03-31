'''
2025-03-30
Author: Dan Schumacher
How to run:
   python ./src/voting.py
'''

import json
from utils.states import GameState, ScreenState, PlayerState
from utils.asthetics import (
    format_gm_message, print_color, clear_screen)

# Load or initialize voting data
def get_voting_data(voting_path: str, round_number: int) -> dict:
    try:
        with open(voting_path, "r") as f:
            vote_dict = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        vote_dict = {}
    round_key = f"votes_r{round_number}"
    if round_key not in vote_dict:
        vote_dict[round_key] = []
    return vote_dict

# Save voting data to file
def save_voting_data(voting_path: str, vote_dict: dict):
    with open(voting_path, "w") as f:
        json.dump(vote_dict, f)

# Display the voting prompt
def display_voting_prompt(gs: GameState, ps:PlayerState) -> str:
    eligible_players = [p for p in gs.players if p.code_code_name != ps.code_name]
    if len(eligible_players) == 0:
        raise ValueError("No eligible players to vote for.")
    

    voting_options = [f"{idx + 1}: {player.code_name}" for idx, player in enumerate(eligible_players)]
    voting_prompt = "\n".join(voting_options)
    return f"Select a player to vote out by number:\n{voting_prompt}\n> "

# Collect the player's vote
def collect_vote(gs: GameState, ps:PlayerState) -> str:
    voting_str = display_voting_prompt(gs, ps)
    while True:
        try:
            vote = int(input(voting_str))
            if 1 <= vote <= len(gs.players):
                return gs.players[vote - 1].code_name
            print_color("Invalid choice. Please enter a number from the list.", "RED")
        except ValueError:
            print_color("Invalid input. Please enter a number.", "RED")

# Count votes and determine the outcome
def count_votes(vote_dict: dict, gs: GameState) -> tuple[str, list]:
    vote_counts = {player.code_name: 0 for player in gs.players}
    round_key = f"votes_r{gs.round_number}"

    for vote in vote_dict[round_key]:
        if vote in vote_counts:
            vote_counts[vote] += 1

    max_votes = max(vote_counts.values())
    voted_out_players = [player for player, count in vote_counts.items() if count == max_votes]
    return max_votes, voted_out_players

# Process the voting result
def process_voting_result(gs: GameState, max_votes: int, voted_out_players: list):
    if len(voted_out_players) > 1:
        gs.last_vote_outcome = "No consensus, no one is voted out this round."
        print_color(format_gm_message(gs.last_vote_outcome), "YELLOW")
    else:
        voted_out_code_name = voted_out_players[0]
        voted_out_player = next((p for p in gs.players if p.code_name == voted_out_code_name), None)

        if voted_out_player:
            gs.players.remove(voted_out_player)
            gs.players_voted_off.append(voted_out_player)
            gs.last_vote_outcome = f"{voted_out_code_name} has been voted out."
            print_color(format_gm_message(gs.last_vote_outcome), "RED")

# Main voting round function
def voting_round(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    input("Press Enter to continue...")
    clear_screen()
    print_color(format_gm_message("It's time to vote! Choose the player you believe is an AI."), "YELLOW")

    # Get voting data
    vote_dict = get_voting_data(gs.voting_path, gs.round_number)

    # Collect and record the vote
    if not ps.voted:
        voted_code_name = collect_vote(gs, ps)
        vote_dict[f"votes_r{gs.round_number}"].append(voted_code_name)
        ps.voted = True
        save_voting_data(gs.voting_path, vote_dict)

    # Check if all human players have voted
    human_players = [p for p in gs.players if p.ai_doppleganger is None]
    if len(vote_dict[f"votes_r{gs.round_number}"]) == len(human_players):
        max_votes, voted_out_players = count_votes(vote_dict, gs)
        process_voting_result(gs, max_votes, voted_out_players)

        # Check if the game should end
        if gs.ice_asked >= (len(gs.players) + len(gs.players_voted_off)) // 2:
            return ScreenState.SCORE, gs, ps
        else:
            return ScreenState.CHAT, gs, ps

    # If voting is not complete, continue the voting state
    return ScreenState.VOTE, gs, ps
