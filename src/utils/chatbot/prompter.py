'''
2025-03-09
Author: Dan Schumacher
How to run:
   python ./src/utils/prompter.py
'''
import os
import json
from dotenv import load_dotenv
from typing import List, Union, Dict
from pydantic import BaseModel
from abc import ABC, abstractmethod
import openai

class QAs(BaseModel):
    question: Dict[str, str]  # Multiple inputs as a dictionary
    answer: str | BaseModel  # Allow both strings and BaseModel

# === Base Prompter Class ===
class Prompter(ABC):
    def __init__(
            self, openai_dict_key: str, system_prompt: str, examples: List[QAs], 
            prompt_headers: Dict[str, str], output_format: BaseModel, 
            main_prompt_header:str, llm_model: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        :param openai_dict_key: API key variable name in .env
        :param system_prompt: System message for the LLM
        :param examples: Few-shot examples (now supports multiple inputs)
        :param prompt_headers: Dictionary mapping field names to headers
        :param output_format: Expected output format (Pydantic model)
        """
        self.api_env_key = openai_dict_key
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.examples = examples  # Keep as list of QAs
        self.main_prompt_header = main_prompt_header
        self.prompt_headers = prompt_headers  # Multiple headers for different input fields
        self.output_format = output_format
        self.temperature = temperature
        self.client = self._load_env()
        if not isinstance(self.prompt_headers, dict):
            raise TypeError(f"Expected `prompt_headers` to be a dictionary, but got {type(self.prompt_headers)} instead: {prompt_headers}")

        self.format_examples()  # Format examples after setting them

    def __repr__(self) -> str:
        return f"Prompter(model={self.llm_model}, examples={len(self.examples)})"

    def _load_env(self) -> str:
        """Loads API key from .env"""
        load_dotenv("./resources/.env")
        api_key = os.getenv(self.api_env_key)
        if not api_key:
            raise ValueError(f"API Key not found. Set {self.api_env_key}=xxxx in ./resources/.env")
        return api_key

    def format_q_as_string(self, question_dict: Dict[str, str]) -> str:
        """Formats multiple question fields for the LLM"""
        formatted_questions = "\n\n".join(
            f"{self.prompt_headers.get(key, key).upper()}: {value}" for key, value in question_dict.items()
        )
        return (
            f"{formatted_questions}\n"
            f"Provide your response **only** in JSON format as shown below:\n"
            f"{self.output_format.model_json_schema()}\n"
            f"Do not include any extra text, explanations, or comments outside the JSON object."
        )

    def format_examples(self):
        """Formats few-shot examples by prepending prompt headers"""
        for qa in self.examples:
            qa.question = {
                key: self.format_q_as_string({key: value}) if isinstance(value, str) else value  #  Preserve dict structure
                for key, value in qa.question.items()
            }
            if isinstance(qa.answer, BaseModel):
                qa.answer = qa.answer.model_dump_json()


    @abstractmethod
    def parse_output(self, llm_output: str):
        """Extract response-text from the LLM output"""
        pass

    @abstractmethod
    def get_completion(self, user_inputs: Dict[str, str]) -> str:
        """Send the prompt to the LLM and get a response"""
        pass

# === OpenAI Implementation ===
class OpenAIPrompter(Prompter):
    def __init__(self, llm_model="gpt-4o-mini", **kwargs):
        super().__init__(**kwargs)
        self.client = openai.Client(api_key=self._load_env())

    def parse_output(self, llm_output) -> list:
        """Extracts the response text from the OpenAI API response"""
        return json.loads(llm_output.choices[0].message.content)

    def _build_messages(self, input_texts: Dict[str, str]):
        """Builds the messages list for the OpenAI API with a single structured user message."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add example QAs (Few-shot learning)
        for qa in self.examples:
            example_lines = []
            for key, value in qa.question.items():
                if isinstance(value, dict):  #  Ensure only dictionaries are unpacked
                    formatted_value = "\n".join(f"{sub_key}: {sub_value}" for sub_key, sub_value in value.items())
                elif isinstance(value, str):  #  Keep JSON strings as-is
                    formatted_value = value
                else:
                    formatted_value = str(value)  # Convert unknown types to string

                example_lines.append(f"{self.prompt_headers.get(key, key)}: {formatted_value}")

            example_text = "\n".join(example_lines)
            messages.append({"role": "user", "content": f"{self.main_prompt_header}\n{example_text}"})
            messages.append({"role": "assistant", "content": qa.answer})

        # Format user input into a single message
        user_input_lines = []
        for key, value in input_texts.items():
            if isinstance(value, dict):
                formatted_value = "\n".join(f"{sub_key}: {sub_value}" for sub_key, sub_value in value.items())
            elif isinstance(value, str):
                formatted_value = value
            else:
                formatted_value = str(value)

            user_input_lines.append(f"{self.prompt_headers.get(key, key)}: {formatted_value}")

        user_input_text = "\n".join(user_input_lines)
        messages.append({"role": "user", "content": f"{self.main_prompt_header}\n{user_input_text}"})

        return messages

    def get_completion(
            self, input_texts: Dict[str, str], parse=True, verbose=False) -> Union[dict, None]:
        """Calls OpenAI API with multiple formatted inputs"""
        input_text_str = self._build_messages(input_texts)
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=input_text_str,
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        final_resp = self.parse_output(response) if parse else response

        if verbose:
            print("\n" + "="*60)
            print("OUTPUT FROM LLM:")
            print(json.dumps(final_resp, indent=4))
            print("="*60 + "\n")

        return final_resp
    
    def fetch_prompt(self, input_texts: Dict[str, str]) -> str:
        """Fetch the prompt without sending it to the LLM."""
        input_text_str = self._build_messages(input_texts)
        return json.dumps(input_text_str, indent=4)