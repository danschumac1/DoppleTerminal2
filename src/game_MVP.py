import asyncio
from datetime import datetime
import os
from prompt_toolkit.shortcuts import PromptSession
from colorama import Fore, Style
from utils.asthetics import format_gm_message
from utils.file_io import load_players_from_lobby
from utils.states import GameState, PlayerState, ScreenState
from utils.constants import COLOR_DICT, ROUND_DURATION

def ask_icebreaker(gs, ps, chat_log):
    intro_msg = format_gm_message(gs.icebreakers[0])
    if ps.timekeeper:
        with open(chat_log, "a", encoding="utf-8") as f:
            f.write(intro_msg)
            f.flush()
    gs.ice_asked += 1
    gs.icebreakers.pop(0)
    print(intro_msg.strip())

async def countdown_timer(duration: int, gs: GameState, ps: PlayerState, chat_log: str):
    elapsed = (datetime.now() - ps.starttime).total_seconds()
    remaining = max(0, duration - int(elapsed))

    if remaining > 0:
        await asyncio.sleep(remaining)

    gs.round_complete = True

    if ps.timekeeper:
        with open(chat_log, "a", encoding="utf-8") as f:
            f.write(format_gm_message("Time's up! Moving to the next round."))
            f.flush()

async def refresh_messages(chat_log, gs: GameState, ps: PlayerState, delay=0.5):
    """Prints only new messages from the chat log."""
    num_lines = 0
    # Check if the file already exists
    if os.path.isfile(chat_log):
        # Get the number of lines in the file
        with open(chat_log, "r", encoding="utf-8") as f:
            num_lines = len(f.readlines())
    while True:
        await asyncio.sleep(delay)
        try:
            with open(chat_log, "r", encoding="utf-8") as f:
                messages = f.readlines()
                
                if len(messages) > num_lines:
                    new_messages = messages[num_lines:]
                    color_formatted_messages = []

                    for msg in new_messages:
                        try:
                            if "GAME MASTER" in msg or "*****" in msg:
                                colored_msg = Fore.YELLOW + msg.strip() + Style.RESET_ALL
                            else:
                                code_name = msg.split(":", 1)[0].strip()
                                player = next((p for p in gs.players if p.code_name == code_name), None)

                                if player:
                                    colored_msg = f"{COLOR_DICT[player.color_name]}{msg.strip()}{Style.RESET_ALL}"
                                else:
                                    colored_msg = msg.strip()

                            color_formatted_messages.append(colored_msg)
                        except Exception as e:
                            print(f"Error formatting message: {msg}, Error: {e}")
                            continue

                    print("\n".join(color_formatted_messages))
                    num_lines = len(messages)

        except FileNotFoundError:
            print("Chat log file not found. Please start a chat session.")
            return
        except IOError as e:
            print(f"Error reading messages: {e}")

ai_response_lock = asyncio.Lock()
async def ai_response(chat_log, ps: PlayerState, delay=1.0):
    """Triggers AI responses only if the last message is not from the AI."""
    ai_name = ps.ai_doppleganger.player_state.code_name
    ps.ai_doppleganger.logger.info(f"AI {ai_name} is inside async def ai_response")
    while True:
        await asyncio.sleep(delay)
        try:
            with open(chat_log, "r", encoding="utf-8") as f:
                messages = f.readlines()

            last_line = messages[-1].strip() if messages else ""
            # Avoid self-reply and ensure the AI is not already responding
            if not last_line.startswith(f"{ai_name}:"):
                ps.ai_doppleganger.logger.info(f"last_line.startswith(f'{ai_name}:') is False")
                full_chat_list = [msg.strip() for msg in messages]

                # Use the async lock to ensure only one response at a time
                async with ai_response_lock:
                    try:
                        ps.ai_doppleganger.logger.info("AI is inside async with ai_response_lock...")
                        # print("Starting AI response generation...")

                        # Run the blocking AI decision in a separate thread and await the result
                        response = await asyncio.wait_for(
                            asyncio.to_thread(
                                ps.ai_doppleganger.decide_to_respond,
                                full_chat_list,
                                chat_log
                            ),
                            timeout=10
                        )

                        # Check if the response is a coroutine and await it if necessary
                        if asyncio.iscoroutine(response):
                            response = await response

                        if response and response != "No response needed.":
                            ai_msg = f"{ai_name}: {response}\n"
                            # print(f"AI RESPONSE: {ai_msg.strip()}")
                            with open(chat_log, "a", encoding="utf-8") as f:
                                ps.ai_doppleganger.logger.info("dumping contents...")
                                # print("AI WROTE TO FILE")
                                f.write(ai_msg)
                                f.flush()

                    except asyncio.TimeoutError:
                        # print(f"AI response took too long, skipping...")
                        ps.ai_doppleganger.logger.info("AI response took too long, skipping...")
                        pass
                    except Exception as e:
                        # print(f"Error during AI response generation: {e}")
                        ps.ai_doppleganger.logger.info(f"Error during AI response generation: {e}")
                        pass

        except IOError as e:
            # print(f"Error in AI response loop: {e}")
            pass

async def user_input(chat_log, ps: PlayerState):
    """Captures user input and writes it to the chat log."""
    session = PromptSession()
    while True:
        try:
            user_message = await session.prompt_async("")
            formatted_message = f"{ps.code_name}: {user_message}\n"
            with open(chat_log, "a", encoding="utf-8") as f:
                f.write(formatted_message)
            # Move the cursor up and clear the line to avoid "You: You:"
            print("\033[A" + " " * len(formatted_message) + "\033[A")
        except Exception as e:
            pass
            # print(f"Error getting user input: {e}")

async def play_game(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    chat_log = gs.chat_log_path
    # Check if the file already exists
    if not os.path.isfile(chat_log):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(chat_log), exist_ok=True)
        # Create the file
        with open(chat_log, "w") as f:
            f.write("")

    # Ask the icebreaker if you are the timekeeper (to avoid duplicate prints)
    if gs.ice_asked <= gs.round_number: # just a safe guard. 
        ask_icebreaker(gs, chat_log)

    try:
        # Start the countdown timer without awaiting it
        asyncio.create_task(countdown_timer(ROUND_DURATION, gs, ps, chat_log))

        # Create independent tasks for each asynchronous function
        message_task = asyncio.create_task(refresh_messages(chat_log, gs, ps))
        ai_task = asyncio.create_task(ai_response(chat_log, ps))
        user_input_task = asyncio.create_task(user_input(chat_log, ps))

        # Continuously check if the round is complete
        while not gs.round_complete:
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting

        # Cancel the ongoing tasks since the round is over
        for task in [message_task, ai_task, user_input_task]:
            task.cancel()
            try:
                await task  # Wait for the cancellation to complete
            except asyncio.CancelledError:
                # print(f"Task {task} successfully cancelled.")
                pass

        # print("Timer ended, moving to the next round.")
        return ScreenState.VOTE, gs, ps

    except asyncio.CancelledError:
        print("\nChat room closed gracefully.")
    except Exception as e:
        print(f"Unexpected error: {e}")
