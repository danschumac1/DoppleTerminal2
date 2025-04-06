
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
from utils.file_io import synchronize_start_time
from colorama import Fore, Style

# Load or initialize voting data
def get_voting_dict(gs:GameState) -> dict:
    # Check if the voting file exists
    if os.path.exists(gs.voting_path):
        # Load existing voting data
        with open(gs.voting_path, 'r') as f:
            vote_dict = json.load(f)
    else:
        # Initialize voting data if file doesn't exist
        vote_dict = {
            'votes_r0': {p.code_name: 0 for p in gs.players}
        }
        # Save the initialized voting data to the file
        with open(gs.voting_path, 'w') as f:
            json.dump(vote_dict, f, indent=4)
    return vote_dict

def update_voting_dict(gs: GameState, code_name:str) -> dict:
    vote_dict = get_voting_dict(gs)
    # Update the voting dictionary with the current round number and players
    round_key = f'votes_r{gs.round_number}'
    if round_key not in vote_dict:
        vote_dict[round_key] = {p.code_name: 0 for p in gs.players}
    # Increment the vote count for the chosen player
    if code_name in vote_dict[round_key]:
        vote_dict[round_key][code_name] += 1
    else:
        raise ValueError(f"Player {code_name} not found in voting dictionary.")
    # Save the updated voting data to the file
    with open(gs.voting_path, 'w') as f:
        json.dump(vote_dict, f, indent=4)
    return vote_dict

# Display the voting prompt
def display_voting_prompt(gs) -> str:
    # Sort players by code name to ensure consistent order for everyone
    eligible_players = sorted(gs.players, key=lambda x: x.code_name)
    voting_options = [f'{idx + 1}: {p.code_name}' for idx, p in enumerate(eligible_players)]
    return f'Select a player to vote out by number:\n' + '\n'.join(voting_options) + '\n> '


# Collect the player's vote
def collect_vote(gs, ps) -> str:
    eligible_players = sorted(gs.players, key=lambda x: x.code_name)
    voting_str = display_voting_prompt(gs)

    while True: 
        try:
            # clear_screen()
            print(format_gm_message(
                "All players present! It's time to vote! Choose the player you most believe is an AI."))
            print(Fore.GREEN + f"remember you are playing as {ps.code_name}".upper() + Style.RESET_ALL)
            vote = int(input(voting_str))

            if 1 <= vote <= len(eligible_players):
                if eligible_players[vote - 1].code_name == ps.code_name:
                    print('You cannot vote for yourself. Please choose another player.')
                    input('Press Enter to try again...')
                    continue
                return eligible_players[vote - 1].code_name

            print('Invalid choice. Please enter a number from the list.')
            input('Press Enter to try again...')
        except ValueError:
            print('Invalid input. Please enter a number.')
            input('Press Enter to try again...')

    
# Count votes and determine the outcome
def count_votes(vote_dict: dict, gs) -> tuple[int, list]:
    round_key = f'votes_r{gs.round_number}'

    current_vote_dict = vote_dict[round_key]
    max_votes = max(current_vote_dict.values())
    players_voted_for_the_most = [p for p, votes in current_vote_dict.items() if votes == max_votes]
    return players_voted_for_the_most, max_votes

# Process the voting result
def process_voting_result(
        gs: GameState, ps: PlayerState, max_votes: int, players_voted_for_the_most: list) -> str:
    # Check for tie or no votes
    if len(players_voted_for_the_most) > 1:
        gs.last_vote_outcome = 'No consensus, no one is voted out this round.'
        result = format_gm_message(gs.last_vote_outcome)
        return result

    # If no votes were cast, no one is voted out
    if max_votes == 0:
        gs.last_vote_outcome = 'No votes were cast, no one is voted out.'
        result = format_gm_message(gs.last_vote_outcome)
        return result

    # If we have a clear winner (only one player with the max votes)
    voted_out_code_name = players_voted_for_the_most[0]
    voted_out_player = next((p for p in gs.players if p.code_name == voted_out_code_name), None)

    if voted_out_player:
        # Mark the voted-out player as no longer in the game in the global state
        # print("THERE IS A VOTE OUT!")
        # print(f"{voted_out_code_name} has been voted out!")

        voted_out_player.still_in_game = False
        gs.players = [p for p in gs.players if p.code_name != voted_out_code_name]
        gs.players_voted_off.append(voted_out_player)
        gs.last_vote_outcome = f'{voted_out_code_name} has been voted out.'
        
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
        else:
            # Display the result for other players
            result = format_gm_message(gs.last_vote_outcome)
        
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
    # Collect the current player's vote if still in the game
    if ps.still_in_game:
        who_player_voted_for = collect_vote(gs, ps)
        round_key = f'votes_r{gs.round_number}'

        # Increment the vote count for the chosen player
        vote_dict = update_voting_dict(gs, who_player_voted_for)
    else:
        print(
            Fore.YELLOW +
            f"YOU ({ps.code_name}) HAVE BEEN VOTED OUT. YOU ARE NOW OBSERVING.".upper() +
            Style.RESET_ALL)

    # Update the list of human players actively in the game
    human_players = [p for p in gs.players if p.is_human and p.still_in_game]


    print('Waiting for all players to vote...')
    print_str = ''
    while True:
        # Refresh the vote data
        vote_dict = get_voting_dict(gs)
        current_round_vote_dict = vote_dict.get(f'votes_r{gs.round_number}', {})

        # Count the total number of votes cast
        num_votes = sum(current_round_vote_dict.values())

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
    players_voted_for_the_most, max_votes = count_votes(vote_dict, gs)
    result = process_voting_result(gs, ps, max_votes, players_voted_for_the_most)

    # Verify if the current player has been voted out
    if ps.code_name not in [p.code_name for p in gs.players if p.still_in_game]:
        ps.still_in_game = False
    dramatic_print(result)

    # Increment the round number after processing the result
    gs.round_number += 1

    # Synchronize the start time for the next round
    synchronize_start_time(gs, ps)

    input(Fore.MAGENTA + "Press Enter to continue to next phase..." + Style.RESET_ALL)
    # clear_screen()

    # Check if we should transition to the score screen
    if should_transition_to_score(gs):
        # clear_screen()
        gs.players = [p for p in gs.players if p.still_in_game]
        return ScreenState.SCORE, gs, ps
    else:
        return ScreenState.CHAT, gs, ps
