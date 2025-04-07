from typing import Optional
from pydantic import BaseModel


class DecideToRespondBM(BaseModel):
    respond_bool:bool
    reasoning: str # Explanation for why this action was chosen

class ActionOptionBM(BaseModel):
    reasoning: Optional[str] = None # Explanation for why this action was chosen
    introduce: Optional[bool] = None
    defend: Optional[bool] = None
    accuse: Optional[bool] = None
    joke: Optional[bool] = None
    question: Optional[bool] = None
    simple_phrase: Optional[bool] = None
    persona_related: Optional[bool] = None
    other: Optional[bool] = None  # Placeholder for any other actions

class IntroBM(BaseModel):
    reasoning: str  # Explanation for why this action was chosen
    output_text: str  # The AI's output for the chat

class DefenseChoices(BaseModel):
    accuse: Optional[str] = None            # Redirect suspicion to another player
    deescalate: Optional[str] = None        # Reduce tension and shift focus
    be_dismissive: Optional[str] = None     # Minimize the accusation’s significance
    counter_evidence: Optional[str] = None  # Use voting history or logic to counter the claim
    seek_alliance: Optional[str] = None     # Convince a neutral player to back you up

    def validate_single_choice(self):
        """Ensures that only ONE choice is made."""
        choices = [self.accuse, self.deescalate, self.be_dismissive, self.counter_evidence, self.seek_alliance]
        non_none_choices = [choice for choice in choices if choice is not None]
        if len(non_none_choices) != 1:
            raise ValueError(f"Only ONE defense choice can be selected. Given: {non_none_choices}")

class DefendYourselfBM(BaseModel):
    accuser: str
    accusation: str
    defense_choice: DefenseChoices
    reasoning: str
    output_text: str # The AI's output for the chat

    def validate_defense(self):
        """Ensures the defense_choice is valid."""
        self.defense_choice.validate_single_choice()

class AccusePlayerBM(BaseModel):
    player_to_accuse: str  # The player being accused
    reasoning: str  # The AI's reasoning for the accusation
    output_text: str  # The AI's output for the chat

# Base Model for Simple Phrases (e.g., "I agree", "lol")
class SimplePhraseBM(BaseModel):
    output_text: str  # The short response AI gives

class JokeBM(BaseModel):
    output_text: str
    reasoning: str  # Why did the AI pick this joke? What does it hope to achieve?
    joke_target: Optional[str] = None  # Is this aimed at a player, game event, or topic?
    joke_tone: Optional[str] = "lighthearted"  # Could be: lighthearted, awkward, self-deprecating, etc.

class QuestionBM(BaseModel):
    output_text: str
    context: Optional[str] = None  # Existing context is still useful
    intent: str  # What does the AI want to achieve with this question?
    target_player: Optional[str] = None  # Who is the question aimed at, if anyone?
    strategy_type: Optional[str] = "information"  # Could be: information, pressure, humor

class OtherBM(BaseModel):
    output_text: str  # Any other action not covered by the above models
    reasoning: str  # Explanation for why this action was chosen

class StylizerBM(BaseModel):
    output_text: str  # The text after applying the stylization

class ValidateResponseBM(BaseModel):
    valid: bool  # Indicates if the response is valid
    reasoning: str  # Explanation for why this response is valid or not