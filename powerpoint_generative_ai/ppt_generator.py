import json
import openai
from .domain.constants import MAX_CONTENT_LENGTH
from .domain.exceptions import InvalidModel
from .domain.prompts import (
    DECK_CREATION_SYSTEM_PROMPT,
    CHART_DATA_IDENTIFICATION,
    BEST_CHART_FOR_DATA_SYSTEM_PROMPT,
    TITLE_GEN_SYSTEM_PROMPT,
    FILENAME_SYSTEM_PROMPT
)
from .ppt.ppt_creator import PowerPointCreator
from .utils.utils import format_simple_message_for_gpt, call_gpt_with_backoff

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
        # identify if the user passed in data for a chart
        data_messages = format_simple_message_for_gpt(
            system_message=CHART_DATA_IDENTIFICATION, user_message=user_input)
        data_response = call_gpt_with_backoff(
            messages=data_messages, temperature=0, max_length=MAX_CONTENT_LENGTH)

        # data was found in the input, determine which chart type fits the data best
        if data_response.lower() == "data found":
            best_chart_messages = format_simple_message_for_gpt(
                system_message=BEST_CHART_FOR_DATA_SYSTEM_PROMPT, user_message=user_input)
            best_chart_response = call_gpt_with_backoff(
                messages=best_chart_messages, temperature=0)
            # append this chart type instruction to the user input for deck creation
            user_input += f"\nUse chart type: {best_chart_response}"

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
