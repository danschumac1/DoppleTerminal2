import time
from colorama import Fore, Style, init
from utils.logging_utils import MasterLogger
from utils.states import ScreenState, PlayerState, GameState

# Initialize Colorama
init(autoreset=True)

def play_intro(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    master_logger = MasterLogger.get_instance()
    master_logger.log("Starting intro screen...")
    
    intro_sections = [
        (Fore.CYAN, """
====================================================================
🌟 WELCOME TO... WHO'S REAL? 🌟
====================================================================
You're a high school student hanging out with your friends during lunch.
Today, you're all playing a social deduction game — but there's a twist..."""),

        (Fore.RED, "Some of your friends have been secretly replaced by AI."),

        (Fore.YELLOW, """
Your job? Figure out who's real and who's not before it's too late."""),

        (Fore.MAGENTA, """
====================================================================
🧠 THE BASICS
====================================================================
- There are 3 human players (including you).
- 3 other players are AI pretending to be humans.
- Chat, observe, and vote to eliminate the AIs."""),

        (Fore.BLUE, """
====================================================================
🔁 GAME FLOW
====================================================================
1. An icebreaker question kicks off each round.
2. Everyone chats, responds, and tries to blend in.
3. At the end of the round, you vote someone out.
4. The game lasts 3 rounds. Win or lose, that’s it."""),

        (Fore.GREEN, """
====================================================================
🎯 HOW TO WIN
====================================================================
- HUMANS win by identifying and voting out all the AIs.
- AIs win if they outnumber the humans by the end."""),

        (Fore.RED, """
====================================================================
⚠️ REMEMBER
====================================================================
- Always stay in character — you're a student, not a machine.
- No swearing or weird behavior.
- Don’t "break the fourth wall" or say things like "as an AI."
- You only know your own identity.
- Convince others that *you* are real, and stay sharp."""),

        (Fore.CYAN, "Ready to enter the game? Let's get your profile set up.\n")
    ]

    for color, section in intro_sections:
        print(color + section)  # Print the section in the specified color
        input("\n(Press Enter to continue...)\n")
        time.sleep(0.1)

    return ScreenState.SETUP, gs, ps