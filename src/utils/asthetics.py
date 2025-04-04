import os
import random
import time
from colorama import Fore, Style

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def dramatic_print(message: str):
    suspense_phrases = [
        "The counsel has decided...",
        "After much deliberation...",
        "The votes have been tallied...",
        "Tension fills the room...",
        "Everyone holds their breath...",
        "A hush falls over the crowd..."
    ]

    # Print a random suspense phrase with some dramatic effect
    phrase = random.choice(suspense_phrases)
    print(Fore.CYAN + phrase + Style.RESET_ALL)

    # Dramatic pause with dots
    for _ in range(3):
        print(Fore.YELLOW + "..." + Style.RESET_ALL, end='', flush=True)
        time.sleep(0.7)

    print("\n")

    # Simulated heartbeat effect
    heartbeat_effect = ["Thump...", "Thump...", "Thump-thump..."]
    for heartbeat in heartbeat_effect:
        print(Fore.RED + heartbeat + Style.RESET_ALL)
        time.sleep(0.6)

    # Final suspense delay
    time.sleep(1)
    print(Fore.GREEN + f"\n{message}\n" + Style.RESET_ALL)

    
def format_gm_message(msg: str) -> str:    
    top = Fore.YELLOW + "*" * 50 + Fore.RESET
    mid = Fore.YELLOW + f"GAME MASTER: {msg}"+ Fore.RESET
    bot = Fore.YELLOW +"*" * 50+ Fore.RESET
    return f"\n\n{top}\n{mid}\n{bot}"

