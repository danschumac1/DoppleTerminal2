import time
from utils.logging_utils import MasterLogger
from utils.states import ScreenState, PlayerState, GameState
# from utils.asthetics import print_color

def play_intro(
    ss: ScreenState, 
    gs: GameState,
    ps: PlayerState,
) -> tuple[ScreenState, GameState, PlayerState]:

    """
    Displays the game introduction, rules, and flavor text, one section at a time.
    """
    master_logger = MasterLogger.get_instance()
    master_logger.log("Starting intro screen...")
    intro_sections = [
        ("CYAN", """
====================================================================
🌟 WELCOME TO... WHO'S REAL? 🌟
===================================================================="""),

        ("YELLOW", """
You're a high school student hanging out with your friends during lunch.
Today, you're all playing a social deduction game — but there's a twist..."""),

        ("RED", "Some of your friends have been secretly replaced by AI."),

        ("YELLOW", """
Your job? Figure out who's real and who's not before it's too late."""),

        ("MAGENTA", """
====================================================================
🧠 THE BASICS
===================================================================="""),

        ("WHITE", """
- There are 3 human players (including you).
- 3 other players are AI pretending to be humans.
- Chat, observe, and vote to eliminate the AIs."""),

        ("BLUE", """
====================================================================
🔁 GAME FLOW
===================================================================="""),

        ("WHITE", """
1. An icebreaker question kicks off each round.
2. Everyone chats, responds, and tries to blend in.
3. At the end of the round, you vote someone out.
4. The game lasts 3 rounds. Win or lose, that’s it."""),

        ("GREEN", """
====================================================================
🎯 HOW TO WIN
===================================================================="""),

        ("WHITE", """
- HUMANS win by identifying and voting out all the AIs.
- AIs win if they outnumber the humans by the end."""),

        ("RED", """
====================================================================
⚠️ REMEMBER
===================================================================="""),

        ("WHITE", """
- Always stay in character — you're a student, not a machine.
- No swearing or weird behavior.
- Don’t "break the fourth wall" or say things like "as an AI."
- You only know your own identity.
- Convince others that *you* are real, and stay sharp."""),

        ("CYAN", "Ready to enter the game? Let's get your profile set up.\n")
    ]

    for color, paragraph in intro_sections:
        # print(print_color(paragraph, color, print_or_return="return"))
        # input(print_color("\n(Press Enter to continue...)\n", "CYAN", print_or_return="return"))
        print(paragraph, color)
        input("\n(Press Enter to continue...)\n")
        time.sleep(0.1)

    return ScreenState.SETUP, gs, ps
