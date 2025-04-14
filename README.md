# DOPPLE BOT: A Social Deduction Game
### Created By: Dan Schumacher Haven Kotara & Kosi 

## Overview
Dopple Bot is a research project for Dr. Fred Martin's Ai4K12 course. 
This game tasks human players with determining who among them is secretly an Ai bot - with a twist!
Unbeknownst to players (initially), these bots are dopplegangers! Not only will human players have to figure out which players are bots, they will have to convince their team that they are the real 'them'. 

Inspired by popular social deception games like Wherewolf and AmongUs, Dopple Bot aims to educate players on the importance of data security and provide an interractive example on how Ai could use their personal information maliciously.

## Usage & Requirements
### Requirements:
- Create a `.env` file in the `Resources` directory; then copy the OpenAi API key into it.
- Create a virtual environment and run the following lines:
    * pip install prompt_toolkit
    * pip install python-dotenv
    * pip install openai==1.58.1
    * pip install colorama
    * pip install windows-curses
- This project requires Python 3.10

### Usage:
In your venv terminal, run the project using: `python src/main.py`

Then the game will begin and take you through the following screens:
- Introduction 
- Info Collection
- Main Game / Chat Room
- Voting
- (Loops through Main and Voting x3 rounds)
- Score Board
- Ending Screen
