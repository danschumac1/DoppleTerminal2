from dataclasses import asdict
from datetime import datetime
import json
import os
from typing import List, Tuple
from time import sleep
from utils.states import GameState, PlayerState

def init_start_time_file(start_time_path: str) -> None:
    """Ensure the start time file exists, initializing if necessary."""
    if not os.path.exists(start_time_path):
        with open(start_time_path, "w") as f:
            json.dump({}, f)
        print(f"Initialized start time file at {start_time_path}.")

def load_start_times(start_time_path: str) -> dict:
    """Load start times from the file."""
    try:
        with open(start_time_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Corrupted or missing start time file, reinitializing...")
        return {}

def save_start_times(start_time_path: str, start_times: dict) -> None:
    """Save start times to the file."""
    with open(start_time_path, "w") as f:
        json.dump(start_times, f, indent=4)

def assign_timekeeper(ps: PlayerState) -> None:
    """Assign the current player as the timekeeper."""
    ps.timekeeper = True
    print(f"{ps.code_name} has been assigned as the timekeeper.")

def set_round_start_time(current_round: str, start_times: dict, start_time_path: str) -> str:
    """Set the start time for the current round."""
    start_time = datetime.now().replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    start_times[current_round] = start_time
    save_start_times(start_time_path, start_times)
    print(f"Set start time for round {current_round}: {start_time}")
    return start_time

def wait_for_start_time(current_round: str, start_time_path: str) -> str:
    """Wait for the timekeeper to set the start time for the current round."""
    while True:
        start_times = load_start_times(start_time_path)
        if current_round in start_times:
            start_time = start_times[current_round]
            print(f"Loaded start time for round {current_round}: {start_time}")
            return start_time
        print(f"Waiting for round {current_round} start time to be set...")
        sleep(1)

def synchronize_start_time(gs: GameState, ps: PlayerState) -> None:
    """
    Synchronizes the start time between players, updating the file only if the player is the timekeeper.
    Other players wait until the new round time is set.
    """
    # Ensure the start time file exists and set timekeeper if needed
    if not os.path.exists(gs.start_time_path):
        init_start_time_file(gs.start_time_path)
        assign_timekeeper(ps)

    # Read the current round number
    current_round = str(gs.round_number)

    # Load existing start times
    start_times = load_start_times(gs.start_time_path)

    # If the file was just created, the player who created it is the timekeeper
    if ps.timekeeper and not start_times:
        print(f"No start times found. Setting initial time for round {current_round}...")
        start_time_str = set_round_start_time(current_round, start_times, gs.start_time_path)
        ps.starttime = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        return

    # Check if the current round time is already set
    if current_round not in start_times:
        if ps.timekeeper:
            # Set the start time if the player is the timekeeper
            start_time_str = set_round_start_time(current_round, start_times, gs.start_time_path)
            ps.starttime = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        else:
            # Wait for the timekeeper to set the start time
            start_time_str = wait_for_start_time(current_round, gs.start_time_path)
            ps.starttime = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    else:
        # If the round time is already set, just load it
        start_time_str = start_times[current_round]
        ps.starttime = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        print(f"Start time for round {current_round} already exists: {start_time_str}")

def init_game_file(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")  # Start fresh

# def append_message(path: str, message: str) -> None:
#     with open(path, "a", encoding="utf-8") as f:
#         f.write(message + "\n")
#         f.flush()
#         os.fsync(f.fileno())

def read_new_messages(path: str, last_line: int) -> Tuple[List[str], List[str], int]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    full_chat_list = [line.strip() for line in lines if line.strip()]
    new_messages_list = full_chat_list[last_line:]
    new_message_count = len(new_messages_list)
    last_line += new_message_count
    return full_chat_list, new_messages_list, last_line

class SequentialAssigner:
    def __init__(self, list_path: str, index_path: str, key: str):
        # print(f"Loading items from {list_path}...")
        self.list_path = list_path
        self.index_path = index_path
        self.key = key
        self.items = self._load_items()

    def _load_items(self) -> List[str]:
        if not os.path.exists(self.list_path):
            raise FileNotFoundError(f"Missing data file: {self.list_path}")

        try:
            with open(self.list_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate the JSON structure
                if self.key not in data or not isinstance(data[self.key], list):
                    raise ValueError(f"Invalid JSON format: {self.key} list not found")
                items = [item.strip().upper() for item in data[self.key] if item.strip()]
        except (json.JSONDecodeError, IOError) as e:
            raise IOError(f"Error reading JSON file: {e}")

        if not items:
            raise ValueError(f"List at {self.list_path} is empty or contains only invalid items.")

        return items

    def _read_index(self) -> int:
        if not os.path.exists(self.index_path):
            return 0

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                idx = int(f.read().strip())
            if not (0 <= idx < len(self.items)):
                raise ValueError("Index out of range.")
            return idx
        except (ValueError, IOError):
            return 0

    def _write_index(self, idx: int):
        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                f.write(str(idx))
        except Exception as e:
            print(f"Error writing index file: {e}")

    def assign(self) -> str:
        idx = self._read_index()
        selected_item = self.items[idx]
        if not selected_item or selected_item not in self.items:
            print(f"Warning: Invalid or empty item selected: '{selected_item}'")
            selected_item = self.items[0]  # Default to the first item as a fallback
        next_idx = (idx + 1) % len(self.items)
        self._write_index(next_idx)

        # Get the caller's file name and line number\
        # FOR DEBUGGING UNCOMMENT BELOW
        # caller_frame = inspect.currentframe().f_back
        # file_name = caller_frame.f_code.co_filename
        # line_number = caller_frame.f_lineno

        # print(f"Assigned {self.key[-1]}: {selected_item} (called from {file_name}, line {line_number})")
        return selected_item


def save_player_to_lobby_file(ps: PlayerState) -> None:
    """
    Save a player to the shared players.json for their lobby.
    """
    lobby_path = f"./data/runtime/lobbies/lobby_{ps.lobby_id}"
    os.makedirs(lobby_path, exist_ok=True)
    file_path = os.path.join(lobby_path, "players.json")

    players = []

    # Load existing players if file exists
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                players = json.load(f)
            except json.JSONDecodeError:
                pass  # start fresh if it's corrupt or empty

    # Avoid duplicates by code_name
    if not any(p["code_name"] == ps.code_name for p in players):
        players.append(asdict(ps))

    # Save updated list
    with open(file_path, "w") as f:
        json.dump(players, f, indent=2)

def load_players_from_lobby(gs:GameState) -> list[PlayerState]:
    if not os.path.exists(gs.player_path):
        return []

    with open(gs.player_path, "r") as f:
        data = json.load(f)
        return [PlayerState(**p) for p in data]
