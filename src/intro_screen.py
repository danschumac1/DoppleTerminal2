import time
from colorama import Fore, Style, init
from utils.asthetics import clear_screen
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

        (Fore.BLUE, """
====================================================================
🧠 THE BASICS
====================================================================
- There are 3 human players (including you).
- 3 other players are AI pretending to be humans.
- Chat, observe, and vote to eliminate the AIs."""),

        (Fore.GREEN, """
====================================================================
🔁 GAME FLOW
====================================================================
1. An icebreaker question kicks off each round.
2. Everyone chats, responds, and tries to blend in.
3. At the end of the round, you vote someone out.
4. The game lasts 3 rounds. Win or lose, that’s it."""),

        (Fore.CYAN, """
====================================================================
🎯 HOW TO WIN
====================================================================
- HUMANS win by identifying and voting out all the AIs.
- AIs win if they outnumber the humans by the end."""),

        (Fore.YELLOW, """
====================================================================
⚠️ REMEMBER
====================================================================
- Always stay in character — you're a student, not a machine.
- No swearing or weird behavior.
- Don’t "break the fourth wall" or say things like "as an AI."
- You only know your own identity.
- Convince others that *you* are real, and stay sharp."""),

        (Fore.GREEN, "Ready to enter the game? Let's get your profile set up.\n" + Style.RESET_ALL)
    ]

    for color, section in intro_sections:
        clear_screen()
        print(color + section)  # Print the section in the specified color
        print("\n\n")
        print(Fore.GREEN + "Intro section complete! Let's Play!")
        input(Fore.MAGENTA + "Press Enter to continue...")
        time.sleep(0.1)
        clear_screen()
    return ScreenState.SETUP, gs, ps