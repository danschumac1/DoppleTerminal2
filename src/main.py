import asyncio
import inspect
from utils.states import ScreenState
from setup import collect_player_data
from intro_screen import play_intro
from game import play_game
from score import score_screen
import inspect
from voting import voting_round
# import signal

# Importing constants and logging
from utils.constants import BLANK_GS, BLANK_PS
from utils.logging_utils import MasterLogger

# async def shutdown(signal, loop):
#     print(f"\nReceived exit signal {signal.name}...")
#     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

#     print(f"Cancelling {len(tasks)} outstanding tasks...")
#     for task in tasks:
#         task.cancel()

#     try:
#         await asyncio.gather(*tasks, return_exceptions=True)
#     except asyncio.CancelledError:
#         print("Tasks cancelled.")
#     finally:
#         print("Closing OpenAI client...")
#         try:
#             from utils.file_io import OpenAIClientManager
#             OpenAIClientManager().close_client()
#             print("OpenAI client closed successfully.")
#         except Exception as e:
#             print(f"Error closing OpenAI client: {e}")

#         print("Shutting down gracefully.")
#         loop.stop()
#         print("Game Exited. Have a great day!")


# def setup_signal_handlers(loop):
#     # Use signal.signal for Windows compatibility
#     signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown(s, loop)))
#     signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(shutdown(s, loop)))


async def main():
    # loop = asyncio.get_running_loop()
    # setup_signal_handlers(loop)

    master_logger = MasterLogger(
        init=True,
        clear=False,
        log_path="./logs/_master.log"
    )
    master_logger.log("Game started - Initializing master logger")

    # Dictionary mapping game states to their corresponding handler functions.
    state_handler = {
        ScreenState.INTRO: play_intro,
        ScreenState.SETUP: collect_player_data,
        ScreenState.CHAT: play_game,
        ScreenState.SCORE: score_screen,
        ScreenState.VOTE: voting_round
    }

    # Initialize the starting screen state and blank game/player states.
    ss = ScreenState.INTRO  # Can also start with ScreenState.INTRO
    gs = BLANK_GS
    ps = BLANK_PS

    # Main game loop
    while True:
        # Check if the current screen state has a handler function.
        if ss in state_handler:
            handler = state_handler[ss]
            
            # Determine if the handler is an asynchronous coroutine.
            if inspect.iscoroutinefunction(handler):
                next_state, next_gs, next_ps = await handler(ss, gs, ps)
            else:
                next_state, next_gs, next_ps = handler(ss, gs, ps)
            
            # Update state variables with the results from the handler.
            ss = next_state
            gs = next_gs
            ps = next_ps
            
            # Log the state transition for debugging and tracking.
            master_logger.log(f"Transitioned to state: {ss}")
        else:
            # Handle unexpected or invalid states.
            master_logger.error(f"Invalid game state encountered: {ss}")
            print("Invalid game state")
            break

if __name__ == "__main__":
    # Run the main game loop using asyncio for asynchronous operations.
    asyncio.run(main())
