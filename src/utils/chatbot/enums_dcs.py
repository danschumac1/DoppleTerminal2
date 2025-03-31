from enum import Enum
from pydantic import BaseModel

class DecideToRespondBM(BaseModel):
    respond_bool:bool
    reasoning: str # Explanation for why this action was chosen

class RespondBM(BaseModel):
    response: str  # The AI's response text
    reasoning: str  # Explanation for why this response was chosen

class StylizerBM(BaseModel):
    output_text: str  # The text after applying the stylization

class ValidateResponseBM(BaseModel):
    valid: bool  # Indicates if the response is valid
    reasoning: str  # Explanation for why this response is valid or not