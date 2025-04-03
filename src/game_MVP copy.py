import asyncio
from prompt_toolkit.shortcuts import PromptSession
import random

with open("chat_log.txt", "w", encoding="utf-8") as f:
    f.write("Chat log initialized.\n\n")

async def refresh_messages(chat_log, delay=0.5):
    """Prints only new messages from the chat log."""
    # Start with an empty chat log with no messages
    num_lines = 0  
    while True:
        # Don't execution if half a second hasn't passed since last execution
        await asyncio.sleep(delay)
        try:
            # Read the chat log file
            with open(chat_log, "r", encoding="utf-8") as f:
                # Read all lines from the file
                messages = f.readlines()
                # IF THERE ARE NEW MESSAGES
                if len(messages) > num_lines:
                    # Gather new messages
                    new_messages = messages[num_lines:]
                    # Print new messages to the console
                    print("".join(new_messages).strip())  # Print new lines
                    # update the number of lines read
                    num_lines = len(messages)  # Update the number of lines read
        except FileNotFoundError:
            print("Chat log file not found. Please start a chat session.")
            return
        except Exception as e:
            print(f"Error reading messages: {e}")

async def ai_response(chat_log, delay=1.0):
    """Generates AI responses only if the last message is not from the AI."""
    # assign the AI a default name
    ai_name = "AI_Bot"
    # use a list of possible responses
    responses = [
        "Interesting!", "I agree.", "Can you explain more?", 
        "That's funny!", "Let's discuss this further.", 
        "I think you might be right.", "Can you elaborate?"
    ]
    # we start with no messages
    num_lines = 0

    while True:
        await asyncio.sleep(delay)
        try:
            with open(chat_log, "r", encoding="utf-8") as f:
                messages = f.readlines()

                # Check if there are enough new messages to respond
                if len(messages) > num_lines + 1:
                    # Get the last non-empty message
                    last_line = messages[-1].strip()
                    # Check if the last message is from the AI itself
                    if not last_line.startswith(f"{ai_name}:"):
                        # Generate an AI response
                        ai_msg = f"{ai_name}: {random.choice(responses)}\n"
                        with open(chat_log, "a", encoding="utf-8") as f:
                            f.write(ai_msg)
                        num_lines = len(messages)  # Update the message count

        except Exception as e:
            print(f"Error in AI response: {e}")

async def user_input(chat_log):
    """Captures user input and writes it to the chat log."""
    session = PromptSession()
    while True:
        try:
            # Await the async prompt
            user_message = await session.prompt_async("")
            # Format the message manually with "You: " and write it to the chat log
            formatted_message = f"You: {user_message}\n"
            with open(chat_log, "a", encoding="utf-8") as f:
                f.write(formatted_message)
            # Clear the prompt to prevent double printing
            print("\033[A" + " " * 50 + "\033[A")
        except Exception as e:
            print(f"Error getting user input: {e}")

async def main():
    chat_log = "chat_log.txt"

    # Create the chat log file if it doesn't exist
    with open(chat_log, "w", encoding="utf-8") as f:
        f.write("")

    # Run the chat room with three concurrent tasks
    await asyncio.gather(
        refresh_messages(chat_log),
        ai_response(chat_log),
        user_input(chat_log)
    )

if __name__ == "__main__":
    asyncio.run(main())
