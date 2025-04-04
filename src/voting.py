
'''
2025-03-30
Author: Dan Schumacher
How to run:
   python ./src/voting.py
'''

import json
import os
from time import sleep
from typing import Tuple
from utils.states import GameState, ScreenState, PlayerState
from utils.asthetics import dramatic_print, format_gm_message, clear_screen
from utils.file_io import load_players_from_lobby, synchronize_start_time
from colorama import Fore, Style

# Load or initialize voting data
def get_voting_data(voting_path: str, round_number: int) -> dict:
    try:
        # try to read the file
        with open(voting_path, 'r') as f:
            vote_dict = json.load(f)
    # if you can't, create an empty dictionary
    except (FileNotFoundError, json.JSONDecodeError):
        vote_dict = {}
    # the key will be the round number
    round_key = f'votes_r{round_number}'
    # that key might already exist, so check for it
    if round_key not in vote_dict:
         # if it doesn't, create an empty list for it
        vote_dict[round_key] = []
    # if it does, do nothing
    return vote_dict

def save_voting_data(voting_path: str, vote_dict: dict):
    try:
        # Load existing votes to avoid overwriting
        if os.path.exists(voting_path):
            with open(voting_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}

    # Merge new votes with existing data
    for round_key, votes in vote_dict.items():
        if round_key in existing_data:
            # Append the new votes to the existing list
            existing_data[round_key].extend(votes)
        else:
            # If the round key doesn't exist, create a new list
            existing_data[round_key] = votes

    # Save the merged data
    with open(voting_path, 'w') as f:
        json.dump(existing_data, f)


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
    # what gets printed to the player before they vote
    voting_str = display_voting_prompt(gs)

    # don't accept crapy invalid inputs
    while True: 
        try:
            # prompt the player to enter a number
            clear_screen()
            print(format_gm_message(
                "All players present! It's time to vote! Choose the player you most believe is an AI."))
            print(Fore.GREEN + f"remember you are playing as {ps.code_name}".upper() + Style.RESET_ALL)
            vote = int(input(voting_str))
            # that number should be between 1 and the number of players
            if 1 <= vote <= len(eligible_players):
                # That number should not vote for themselves
                if eligible_players[vote - 1].code_name == ps.code_name:
                    print('You cannot vote for yourself. Please choose another player.')
                    input('Press Enter to try again...')
                # finally, return the code name of the player they voted for
                return eligible_players[vote - 1].code_name
            # if we get here the input was a wrong number
            print('Invalid choice. Please enter a number from the list.')
            input('Press Enter to try again...')

        # if the input was not a number, we want to catch that too
        except ValueError:
            print('Invalid input. Please enter a number.')
            input('Press Enter to try again...')

# Count votes and determine the outcome
def count_votes(vote_dict: dict, gs: GameState) -> tuple[int, list]:
    # Initialize a dictionary to count votes for each player
    vote_counts = {player.code_name: 0 for player in gs.players}
    round_key = f'votes_r{gs.round_number}'

    # Retrieve votes from the dictionary, default to an empty list if not found
    votes = vote_dict.get(round_key, [])
    if not votes:  # No votes were cast
        return 0, []

    # Tally the votes
    for voted_name in votes:
        if voted_name in vote_counts:
            vote_counts[voted_name] += 1

    max_votes = max(vote_counts.values())
    # Find players with the maximum number of votes
    voted_out_players = [player for player, count in vote_counts.items() if count == max_votes]

    # If everyone tied with 0 votes, no one should be voted out
    if max_votes == 0:
        return 0, []

    return max_votes, voted_out_players

# Process the voting result
def process_voting_result(
        gs: GameState, ps: PlayerState, max_votes: int, voted_out_players: list) -> str:
    # Check for tie or no votes
    if len(voted_out_players) > 1:
        gs.last_vote_outcome = 'No consensus, no one is voted out this round.'
        result = format_gm_message(gs.last_vote_outcome)
        return result

    # If no votes were cast, no one is voted out
    if max_votes == 0:
        gs.last_vote_outcome = 'No votes were cast, no one is voted out.'
        result = format_gm_message(gs.last_vote_outcome)
        return result

    # If we have a clear winner (only one player with the max votes)
    voted_out_code_name = voted_out_players[0]
    voted_out_player = next((p for p in gs.players if p.code_name == voted_out_code_name), None)

    if voted_out_player:
        # Mark the voted-out player as no longer in the game in the global state
        voted_out_player.still_in_game = False
        gs.players.remove(voted_out_player)
        gs.players_voted_off.append(voted_out_player)
        gs.last_vote_outcome = f'{voted_out_code_name} has been voted out.'
        result = format_gm_message(gs.last_vote_outcome)
        
        # Update the specific player state if the current player is the one voted out
        if ps.code_name == voted_out_code_name:
            ps.still_in_game = False
            result = (
                Fore.RED +
                "****************************************************************\n" +
                f'You {ps.code_name} have been voted out! Please stay and observe'.upper() + "\n" +
                "****************************************************************" +
                Style.RESET_ALL
            )
        
        return result

    # In case no valid result was formed
    return format_gm_message("Unexpected error: No valid voting result.")



def should_transition_to_score(gs: GameState) -> bool:
    # Condition 1: No human players left
    human_players = [p for p in gs.players if p.is_human]
    if len(human_players) == 0:
        print(format_gm_message('All human players have been voted out. Transitioning to score screen...'))
        return True

    # Condition 2: No AI players left
    ai_players = [p for p in gs.players if not p.is_human]
    if len(ai_players) == 0:
        print(format_gm_message('All AI players have been voted out. Transitioning to score screen...'))
        return True

    # Condition 3: At least half of the total players have been voted out
    if gs.round_number >= gs.number_of_human_players:
        print(format_gm_message(f'{gs.round_number} Rounds have passed. Transitioning to score screen...'))
        return True
    return False


# Main voting round function
def voting_round(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    print(format_gm_message('Waiting for players to be ready to vote...'))
    print_str = ''

    # Wait for all players to be ready to vote
    while len(gs.players) < gs.number_of_human_players:
        sleep(1)
        gs.players = load_players_from_lobby(gs)
        human_players = [p for p in gs.players if p.is_human and p.still_in_game]
        new_str = f'{len(human_players)}/{gs.number_of_human_players} players are ready to vote.'
        if print_str != new_str:
            print(new_str)
            print_str = new_str

    # Initialize the voting data
    vote_dict = get_voting_data(gs.voting_path, gs.round_number)

    # Collect the current player's vote if still in the game
    if ps.still_in_game:
        who_player_voted_for = collect_vote(gs, ps)
        round_key = f'votes_r{gs.round_number}'

        # Ensure the vote is only recorded once per player
        if who_player_voted_for not in vote_dict.get(round_key, []):
            vote_dict.setdefault(round_key, []).append(who_player_voted_for)
            ps.voted = True
            save_voting_data(gs.voting_path, vote_dict)
        else:
            print(format_gm_message(f"Vote already cast for this round by {ps.code_name}."))
    else:
        print(
            Fore.YELLOW +
            f"YOU ({ps.code_name}) HAVE BEEN VOTED OUT. YOU ARE NOW OBSERVING.".upper() +
            Style.RESET_ALL)

    # Update the list of human players actively in the game
    human_players = [p for p in gs.players if p.is_human and p.still_in_game]

    print('Waiting for all players to vote...')

    # Waiting for all votes to be cast
    while True:
        # Refresh the vote data
        vote_dict = get_voting_data(gs.voting_path, gs.round_number)
        votes = vote_dict.get(f'votes_r{gs.round_number}', [])

        # Count the total number of votes cast
        num_votes = len(votes)

        # Update the printed message only if it changes
        new_str = f'{num_votes}/{len(human_players)} players have voted.'
        if print_str != new_str:
            print(new_str)
            print_str = new_str

        # Check if we have collected votes from all players
        if num_votes >= len(human_players):
            break

        # Add a small delay to reduce CPU usage
        sleep(1)

    print('All votes received. Proceeding to counting...')

    # Count votes and process the result
    max_votes, voted_out_players = count_votes(vote_dict, gs)
    result = process_voting_result(gs, ps, max_votes, voted_out_players)

    # Verify if the current player has been voted out
    if ps.code_name not in [p.code_name for p in gs.players if p.still_in_game]:
        ps.still_in_game = False
    dramatic_print(result)

    # Increment the round number after processing the result
    gs.round_number += 1

    # Synchronize the start time for the next round
    synchronize_start_time(gs, ps)

    input(Fore.MAGENTA + "Press Enter to continue to next phase..." + Style.RESET_ALL)
    clear_screen()

    # Check if we should transition to the score screen
    if should_transition_to_score(gs):
        clear_screen()

        return ScreenState.SCORE, gs, ps
    else:
        return ScreenState.CHAT, gs, ps
