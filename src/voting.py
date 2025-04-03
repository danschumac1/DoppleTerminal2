
'''
2025-03-30
Author: Dan Schumacher
How to run:
   python ./src/voting.py
'''

import json
import os
from time import sleep
from utils.states import GameState, ScreenState, PlayerState
from utils.asthetics import format_gm_message, clear_screen
from utils.file_io import load_players_from_lobby, init_game_file

# Load or initialize voting data
def get_voting_data(voting_path: str, round_number: int) -> dict:
    try:
        with open(voting_path, 'r') as f:
            vote_dict = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        vote_dict = {}
    round_key = f'votes_r{round_number}'
    if round_key not in vote_dict:
        vote_dict[round_key] = []
    return vote_dict

# Save voting data to file
def save_voting_data(voting_path: str, vote_dict: dict):
    with open(voting_path, 'w') as f:
        json.dump(vote_dict, f)

# Display the voting prompt
def display_voting_prompt(gs: GameState) -> str:
    # Sort players by code name to ensure consistent order for everyone
    eligible_players = sorted(gs.players, key=lambda x: x.code_name)
    voting_options = [f'{idx + 1}: {p.code_name}' for idx, p in enumerate(eligible_players)]
    return f'Select a player to vote out by number:\n' + '\n'.join(voting_options) + '\n> '


# Collect the player's vote
def collect_vote(gs: GameState, ps: PlayerState) -> str:
    # Use the consistent list for everyone
    eligible_players = sorted(gs.players, key=lambda x: x.code_name)
    voting_str = display_voting_prompt(gs)
    while True:
        try:
            vote = int(input(voting_str))
            if 1 <= vote <= len(eligible_players):
                return eligible_players[vote - 1].code_name
            print('Invalid choice. Please enter a number from the list.')
        except ValueError:
            print('Invalid input. Please enter a number.')

# Count votes and determine the outcome
def count_votes(vote_dict: dict, gs: GameState) -> tuple[str, list]:
    vote_counts = {player.code_name: 0 for player in gs.players}
    round_key = f'votes_r{gs.round_number}'

    for vote in vote_dict.get(round_key, []):
        if vote in vote_counts:
            vote_counts[vote] += 1

    max_votes = max(vote_counts.values())
    voted_out_players = [player for player, count in vote_counts.items() if count == max_votes]
    return max_votes, voted_out_players

# Process the voting result
def process_voting_result(gs: GameState, max_votes: int, voted_out_players: list):
    if len(voted_out_players) > 1:
        gs.last_vote_outcome = 'No consensus, no one is voted out this round.'
        print(format_gm_message(gs.last_vote_outcome))
    else:
        voted_out_code_name = voted_out_players[0]
        voted_out_player = next((p for p in gs.players if p.code_name == voted_out_code_name), None)

        if voted_out_player:
            gs.players.remove(voted_out_player)
            gs.players_voted_off.append(voted_out_player)
            gs.last_vote_outcome = f'{voted_out_code_name} has been voted out.'
            print(format_gm_message(gs.last_vote_outcome))

# Main voting round function
def voting_round(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    print(format_gm_message('Waiting for players to be ready to vote...'))
    print_str = ''
    retry_count = 0
    max_retries = 30

    while len(gs.players) < gs.number_of_human_players:
        sleep(1)
        gs.players = load_players_from_lobby(gs)
        human_players = [p for p in gs.players if not p.ai_doppleganger]
        new_str = f'{len(human_players)}/{gs.number_of_human_players} players are ready to vote.'
        if print_str != new_str:
            print(new_str)
            print_str = new_str
        retry_count += 1
        if retry_count >= max_retries:
            print(format_gm_message("Timeout: Not all players are ready. Proceeding with available players."))
            break

    input('Press Enter to start voting...')
    clear_screen()
    print(format_gm_message("It's time to vote! Choose the player you believe is an AI."))

    vote_dict = get_voting_data(gs.voting_path, gs.round_number)

    if not ps.voted:
        voted_code_name = collect_vote(gs, ps)
        vote_dict.setdefault(f'votes_r{gs.round_number}', []).append(voted_code_name)
        ps.voted = True
        save_voting_data(gs.voting_path, vote_dict)

    human_players = [p for p in gs.players if p.is_human]
    retry_count = 0

    while len(vote_dict[f'votes_r{gs.round_number}']) < len(human_players):
        print('Waiting for all players to vote...')
        sleep(1)
        vote_dict = get_voting_data(gs.voting_path, gs.round_number)
        retry_count += 1
        if retry_count >= max_retries:
            print(format_gm_message("Timeout: Proceeding with available votes."))
            break

    max_votes, voted_out_players = count_votes(vote_dict, gs)
    process_voting_result(gs, max_votes, voted_out_players)

    if gs.ice_asked >= (len(gs.players) + len(gs.players_voted_off)) // 2:
        return ScreenState.SCORE, gs, ps
    else:
        return ScreenState.CHAT, gs, ps
