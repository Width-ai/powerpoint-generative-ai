import re
import backoff
import logging
import openai
from typing import List
import requests
import base64, zlib

def setup_logger(name) -> logging.Logger:
    """
    Sets up a logger instance with a set log format
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a formatter for the log messages
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    # Create a console handler for the log messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger(__name__)


def format_simple_message_for_gpt(system_message: str, user_message: str) -> List[dict]:
    """
    Takes in a single system message and user message and returns a 
    list of messages used for gpt chat completion
    """
    return [
        {
            "role": "system",
            "content": system_message
        },
        {
            "role": "user",
            "content": user_message
        }
    ]


@backoff.on_exception(backoff.expo, openai.error.OpenAIError, logger=logger)
def call_gpt_with_backoff(messages: List, model: str = "gpt-4", temperature: float = 0.7, max_length: int = 256) -> str:
    """
    Function to call GPT4 and handle exceptions with an exponential backoff. This is best used when retrying during high demand
    """
    response = call_gpt(
        messages=messages,
        model=model,
        temperature=temperature,
        max_length=max_length
    )
    return response


def call_gpt(messages: List, model: str = "gpt-4", temperature: float = 0.7, max_length: int = 256) -> str:
    """
    Generic function to call GPT4 with specified messages
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_length,
        frequency_penalty=0.0,
        top_p=1
    )
    return response['choices'][0]['message']['content']


def parse_function_call_output(input_text: str) -> list[str]:
    """
    Removes the <THINK> tags from the input_text, clean it and return the function name and params.
    """

    pattern = "<THINK>.*?</THINK>"
    cleaned_text = re.sub(pattern, '', input_text, flags=re.DOTALL)
    text = cleaned_text.replace("<out>", "").replace("</out>", "").strip()
   
    functions_calls = text.split("\n")
    parsed_functions_calls = []
    for function_call in functions_calls:
        function_name = function_call.split("|")[1]
        param = function_call.split("|")[2]

        parsed_functions_calls.append([function_name, param])

    return parsed_functions_calls


def generate_mermaid_diagram(mermaid_text: str, filename: str = "diagram.png"):
    """
    Takes in mermaid syntax text and generates a diagram
    """

    encoded_mermaid_text = base64.urlsafe_b64encode(zlib.compress(mermaid_text.encode("utf-8"), 9)).decode("ascii")
    url = f"https://kroki.io/mermaid/png/{encoded_mermaid_text}"
    response = requests.get(url)

    with open(filename, "wb") as f:
        f.write(response.content)
    
    return filename
