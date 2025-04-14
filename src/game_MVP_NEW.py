import asyncio
import curses
import os
import re
from datetime import datetime
from utils.asthetics import format_gm_message
from utils.constants import COLOR_DICT, ROUND_DURATION
from utils.states import GameState, PlayerState, ScreenState

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def ask_icebreaker(gs, ps, chat_log):
    intro_msg = format_gm_message(gs.icebreakers[0])
    if ps.timekeeper:
        with open(chat_log, "a", encoding="utf-8") as f:
            f.write(strip_ansi(intro_msg) + "\n")
            f.flush()
    gs.ice_asked += 1
    gs.icebreakers.pop(0)

def cleanup(stdscr):
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

async def chat_ui(chat_log, ps: PlayerState, gs: GameState):
    def setup_windows():
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        
        # Initialize color pairs for players
        for index, (name, color) in enumerate(COLOR_DICT.items(), start=1):
            curses.init_pair(index, index, curses.COLOR_BLACK)

        height, width = stdscr.getmaxyx()
        input_win = curses.newwin(3, width, height - 3, 0)
        chat_win = curses.newwin(height - 3, width, 0, 0)

        input_win.keypad(1)
        input_win.border()

        return stdscr, chat_win, input_win

    async def handle_input(input_win):
        current_input = []
        while True:
            input_win.clear()
            input_win.border()
            input_win.addstr(1, 1, f"{ps.code_name}: {''.join(current_input)}")
            input_win.refresh()

            char = input_win.getch()
            if char in (10, 13):  # Enter
                if current_input:
                    message = f"{ps.code_name}: {''.join(current_input)}\n"
                    with open(chat_log, "a", encoding="utf-8") as f:
                        f.write(message)
                    current_input = []
            elif char in (127, curses.KEY_BACKSPACE):
                if current_input:
                    current_input.pop()  # Remove the last character
            elif 32 <= char <= 126:
                current_input.append(chr(char))  # Add character to input
            await asyncio.sleep(0.01)

    async def update_chat(chat_win):
        last_line_count = 0
        while True:
            try:
                with open(chat_log, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if len(lines) != last_line_count:
                    chat_win.clear()
                    height, width = chat_win.getmaxyx()
                    visible_lines = lines[-(height - 2):]

                    for idx, line in enumerate(visible_lines):
                        clean_line = strip_ansi(line.strip())

                        if "GAME MASTER" in clean_line or "*****" in clean_line:
                            chat_win.addstr(idx + 1, 1, clean_line[:width - 2], curses.color_pair(1))
                            continue

                        for name in COLOR_DICT.keys():
                            if clean_line.startswith(f"{name}:"):
                                color_id = list(COLOR_DICT.keys()).index(name) + 1
                                chat_win.addstr(idx + 1, 1, clean_line[:width - 2], curses.color_pair(color_id))
                                break
                        else:
                            chat_win.addstr(idx + 1, 1, clean_line[:width - 2])

                    chat_win.refresh()
                    last_line_count = len(lines)
            except Exception:
                pass
            await asyncio.sleep(0.2)

    stdscr = None
    try:
        stdscr, chat_win, input_win = setup_windows()
        await asyncio.gather(
            handle_input(input_win),
            update_chat(chat_win)
        )
    except Exception as e:
        if stdscr:
            cleanup(stdscr)
        print(f"Error: {e}")
    finally:
        if stdscr:
            cleanup(stdscr)

async def countdown_timer(duration: int, gs: GameState, ps: PlayerState, chat_log: str):
    elapsed = (datetime.now() - ps.starttime).total_seconds()
    remaining = max(0, duration - int(elapsed))
    if remaining > 0:
        await asyncio.sleep(remaining)
    gs.round_complete = True
    if ps.timekeeper:
        with open(chat_log, "a", encoding="utf-8") as f:
            f.write(strip_ansi(format_gm_message("Time's up! Moving to the next round.")) + "\n")
            f.flush()

async def ai_response(chat_log, ps: PlayerState, delay=1.0):
    ai_name = ps.ai_doppleganger.player_state.code_name
    while True:
        await asyncio.sleep(delay)
        try:
            with open(chat_log, "r", encoding="utf-8") as f:
                messages = f.readlines()

            last_line = messages[-1].strip() if messages else ""
            if not last_line.startswith(f"{ai_name}:"):
                full_chat_list = [msg.strip() for msg in messages]
                async with ai_response_lock:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            ps.ai_doppleganger.decide_to_respond,
                            full_chat_list,
                            chat_log
                        ),
                        timeout=10
                    )
                    if asyncio.iscoroutine(response):
                        response = await response
                    if response and response != "No response needed.":
                        ai_msg = f"{ai_name}: {response}\n"
                        with open(chat_log, "a", encoding="utf-8") as f:
                            f.write(ai_msg)
                            f.flush()
        except Exception:
            pass

ai_response_lock = asyncio.Lock()

async def play_game(ss: ScreenState, gs: GameState, ps: PlayerState) -> tuple[ScreenState, GameState, PlayerState]:
    chat_log = gs.chat_log_path
    os.makedirs(os.path.dirname(chat_log), exist_ok=True)
    if not os.path.isfile(chat_log):
        with open(chat_log, "w") as f:
            f.write("")

    if gs.ice_asked <= gs.round_number:
        ask_icebreaker(gs, ps, chat_log)

    try:
        timer_task = asyncio.create_task(countdown_timer(ROUND_DURATION, gs, ps, chat_log))
        ai_task = asyncio.create_task(ai_response(chat_log, ps))
        ui_task = asyncio.create_task(chat_ui(chat_log, ps, gs))

        while not gs.round_complete:
            await asyncio.sleep(0.1)

        for task in [timer_task, ai_task, ui_task]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        return ScreenState.VOTE, gs, ps

    except asyncio.CancelledError:
        return ScreenState.VOTE, gs, ps
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ScreenState.VOTE, gs, ps