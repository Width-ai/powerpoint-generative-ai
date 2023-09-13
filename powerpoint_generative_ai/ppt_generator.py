import json
import openai
from .domain.constants import MAX_CONTENT_LENGTH
from .domain.exceptions import InvalidModel
from .domain.prompts import (
    DECK_CREATION_SYSTEM_PROMPT,
    TITLE_GEN_SYSTEM_PROMPT,
    FILENAME_SYSTEM_PROMPT,
    TOOL_USE_PROMPT
)
from .ppt.ppt_creator import PowerPointCreator
from .utils.utils import format_simple_message_for_gpt, call_gpt_with_backoff, generate_mermaid_diagram, parse_function_call_output

class PowerPointGenerator:
    def __init__(self, openai_key: str, model: str = "gpt-4"):
        openai.api_key = openai_key
        if model not in [model.id for model in openai.Model.list()['data']]:
            raise InvalidModel(
                f"Model {model} not found in list of models from OpenAI, make sure the "
                "name is correct or you have access to the model requested"
            )
        self.model = model

    def create_powerpoint(self, user_input: str) -> str:
        """Generates a powerpoint based on the user's input"""
        data_messages = format_simple_message_for_gpt(
            system_message=TOOL_USE_PROMPT, 
            user_message=f"This is the user input: \n{user_input}\n Analyze this and output in the given format.")
        data_response = call_gpt_with_backoff(
            messages=data_messages, temperature=0, max_length=MAX_CONTENT_LENGTH)
        
        
        func, param = parse_function_call_output(data_response)
        if func != "none":
            if func == "generate_chart":
                best_chart_response = param
                user_input += f"\nUse chart type: {best_chart_response}"
            elif func == "generate_mermaid_diagram":
                mermaid_text, name = param.split("@,@")
                generate_mermaid_diagram(mermaid_text=mermaid_text, filename=name+'.png')
                user_input += f"\We have a diagram named: '{name}.png'. \n Use it in the powerpoint."

        # create the deck based on the user input and load its json
        deck_messages = format_simple_message_for_gpt(
            system_message=DECK_CREATION_SYSTEM_PROMPT, user_message=user_input)
        deck_response = call_gpt_with_backoff(
            messages=deck_messages, temperature=0.2, max_length=MAX_CONTENT_LENGTH)
        deck_json = json.loads(deck_response)

        # create a fitting title for the deck
        title_messages = format_simple_message_for_gpt(
            system_message=TITLE_GEN_SYSTEM_PROMPT, user_message=deck_response)
        title_response = call_gpt_with_backoff(messages=title_messages)
        title_response = title_response.replace('"', '')

        # create a filename to save the deck as
        filename_message = format_simple_message_for_gpt(
            system_message=FILENAME_SYSTEM_PROMPT, user_message=title_response)
        filename_response = call_gpt_with_backoff(
            messages=filename_message, temperature=0)
        filename_response = filename_response.replace('"', '')

        # create the generated deck and save it to the specified filename
        ppt = PowerPointCreator(title=title_response, slides_content=deck_json)
        ppt.create(file_name=filename_response)
        return filename_response
