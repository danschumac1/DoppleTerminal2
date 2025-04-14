import asyncio
import inspect
import random
from utils.states import ScreenState
from setup import collect_player_data
from intro_screen import play_intro
from game_MVP import play_game    # New screen uses curses for separate input spot
# from game_MVP_NEW import play_game
# from fake_chat import play_game # FOR DEBUGGING
from score_NEW import score_screen
import inspect
from voting import voting_round
# import signal

# Importing constants and logging
from utils.constants import BLANK_GS, BLANK_PS, ICEBREAKERS
from utils.logging_utils import MasterLogger

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
    ss = ScreenState.INTRO
    # ss = ScreenState.SETUP    ## DEBUG: Skips INTRO and moves to player setup
    gs = BLANK_GS
    icebreakers = ICEBREAKERS[1:]
    first_breaker = ICEBREAKERS[0]
    random.shuffle(icebreakers)
    icebreakers.insert(0, first_breaker)
    gs.icebreakers = ICEBREAKERS
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
