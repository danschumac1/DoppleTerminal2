from datetime import datetime
import asyncio
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import ANSI

from utils.asthetics import (
    format_gm_message, 
    # get_color_for_code_name, print_color
    )
from utils.logging_utils import MasterLogger
from utils.states import GameState, ScreenState, PlayerState
from utils.constants import ROUND_DURATION

from utils.file_io import (
    append_message, read_new_messages, load_players_from_lobby
)

# Helper function to print an icebreaker question
def ask_icebreaker(gs):
    if gs.ice_asked >= gs.round_number:
        return  # Don't ask again if already asked
    intro_msg = format_gm_message(gs.icebreakers[0])
    gs.ice_asked += 1
    gs.icebreakers.pop(0)
    append_message(
        gs.chat_log_path, format_gm_message(intro_msg))


# Countdown timer with synchronized start time
async def countdown_timer(duration: int, gs: GameState, ps: PlayerState):
    elapsed = (datetime.now() - ps.starttime).total_seconds()
    remaining = max(0, duration - int(elapsed))

    await asyncio.sleep(remaining)
    gs.round_complete = True

    if ps.timekeeper:
        # print_color(format_gm_message("Time's up! Moving to the next round."), "YELLOW")
        print(format_gm_message("Time's up! Moving to the next round."))

# Refresh the chat log and print new messages
async def refresh_messages_loop(
    chat_log_path: str, gs: GameState, ps: PlayerState, delay: float = 0.5):
    last_line = 0
    session = PromptSession()
    while True:
        await asyncio.sleep(delay)
        try:
            with open(chat_log_path, "r", encoding="utf-8") as f:
                # Read all lines from the file
                lines = f.readlines()
                # Extract only new lines since the last read
                new_msgs = lines[last_line:]
                # Update the last line number
                last_line = len(lines)

                if new_msgs:
                    gs.players = load_players_from_lobby(gs)
                    formatted_msgs = []
                    for msg in new_msgs:
                        if "GAME MASTER" in msg or "*****" in msg:
                            formatted_msgs.append(format_gm_message(msg))
                        else:
                            # code_name = msg.split(":", 1)[0]
                            try:
                                formatted_msgs.append(msg.strip())  # Strip to remove extra newlines
                            except Exception as e:
                                print(f"Error processing message: {msg}, Error: {e}")
                                continue
                    # Print all formatted messages at once to prevent overlapping
                    print("\n".join(formatted_msgs))
                    # Refresh the prompt after printing AI messages
                    session.app.invalidate()
        except Exception as e:
            print(f"Error reading messages: {e}")



# AI loop to handle AI responses
async def ai_loop(ps: PlayerState, gs, master_logger: MasterLogger, delay: float = 0.25) -> None:
    last_message_count = 0
    ai_code_name = ps.ai_doppleganger.player_state.code_name

# try:
    while True:
        full_chat_list, _, num_new_messages = read_new_messages(gs.chat_log_path, last_message_count)

        if num_new_messages:
            last_line = full_chat_list[-1] if full_chat_list else ""
            if last_line.startswith(f"{ai_code_name}:"):
                await asyncio.sleep(delay)
                last_message_count = num_new_messages
                continue

            last_message_count = num_new_messages

            ai_response = ps.ai_doppleganger.decide_to_respond(full_chat_list)

            if ai_response and not ai_response.startswith("Wait for"):
                ai_msg = f"{ai_code_name}: {ai_response}"
                append_message(gs.chat_log_path, ai_msg)
                master_logger.log(f"[AI] {ai_code_name} responded: {ai_response}")
                ps.logger.info(f"[AI] {ai_code_name} responded: {ai_response}")

        await asyncio.sleep(delay)

    # except asyncio.CancelledError:
    #     print(f"AI loop for {ai_code_name} cancelled.")
    # finally:
    #     print(f"AI loop for {ai_code_name} terminated gracefully.")


# Handle user input
# Handle user input
async def user_input_loop(session, chat_log_path, gs, ps, master_logger):
    try:
        while True:
            try:
                # Properly await the async prompt
                user_input = await session.prompt_async(f"{ps.code_name}: ")
                if user_input == "exit":
                    return ScreenState.SCORE, ps, gs
                if ":" in user_input.strip().lower():
                    print("Invalid input. Please do not include a colon in your message.")
                    continue

                player_msg = f"{ps.code_name}: {user_input}"
                append_message(chat_log_path, player_msg)
                master_logger.log(f"[User] {ps.code_name} sent: {user_input}")
                ps.logger.info(f"[User] {ps.code_name} sent: {user_input}")
            except KeyboardInterrupt:
                print("\nUser input interrupted. Exiting input loop.")
                break
            except Exception as e:
                print(f"Error receiving input: {e}")
    except asyncio.CancelledError:
        print("\nUser input loop cancelled gracefully.")        

# Main game loop
async def play_game(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    if ps.timekeeper and gs.ice_asked <= gs.round_number:
        ask_icebreaker(gs)
    session = PromptSession()
    master_logger = MasterLogger.get_instance()

    refresh_task = asyncio.create_task(refresh_messages_loop(gs.chat_log_path, gs, ps))
    round_duration = ROUND_DURATION
    timer_task = asyncio.create_task(countdown_timer(round_duration, gs, ps))

    try:
        _, pending = await asyncio.wait(
            [
                asyncio.create_task(ai_loop( ps,gs, master_logger)),
                asyncio.create_task(user_input_loop(session, gs.chat_log_path,gs, ps , master_logger)),
                timer_task
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

    except asyncio.CancelledError:
        pass
    finally:
        refresh_task.cancel()
        timer_task.cancel()
        await asyncio.sleep(0.1)

    if gs.round_complete:
        return ScreenState.VOTE, gs, ps


    return ScreenState.CHAT, gs, ps
