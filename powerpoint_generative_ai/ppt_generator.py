import json
from typing import Union
import openai
from .domain.constants import MAX_CONTENT_LENGTH
from .domain.exceptions import InvalidModel
from .domain.prompts import (
    DECK_CREATION_SYSTEM_PROMPT,
    TITLE_GEN_SYSTEM_PROMPT,
    FILENAME_SYSTEM_PROMPT,
    TOOL_USE_PROMPT,
    SLIDE_CREATION_PROMPT
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
    # str or list user_input
    def create_powerpoint(self, user_input: Union[str, list]) -> str:
        """Generates a powerpoint based on the user's input"""
        data_messages = format_simple_message_for_gpt(
            system_message=TOOL_USE_PROMPT, 
            user_message=f"This is the user input: \n{user_input}\n Analyze this and output in the given format.")
        data_response = call_gpt_with_backoff(
            messages=data_messages, temperature=0, max_length=MAX_CONTENT_LENGTH)
        
        
        calls = parse_function_call_output(data_response)

        diagrams = []
        for func, param in calls:
            if func != "none":
                if func == "generate_chart":
                    best_chart_response = param
                    user_input += f"\nUse chart type: {best_chart_response}"
                elif func == "generate_mermaid_diagram":
                    mermaid_text, name = param.split("@,@")
                    resp = generate_mermaid_diagram(mermaid_text=mermaid_text, filename=name+'.png')
                    if resp is None:
                        continue
                    diagrams.append(name)
        
        if diagrams != []:
            diagrams = "\n".join([diagram+'.png' for diagram in diagrams])

            user_input += f"""
                We have some diagrams named:

                {diagrams}

                You can use them in your powerpoint."""

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


    def create_powerpoint_from_outline(self, outline: list) -> str:
        
        deck = []
        for slide in outline:
            user_input = slide
            data_messages = format_simple_message_for_gpt(
                system_message=TOOL_USE_PROMPT + "\n\n Not that there is no need to generate a diagram unless user asks you to generate one.", 
                user_message=f"This is the user input: \n{user_input}\n Analyze this and output in the given format.")
            data_response = call_gpt_with_backoff(
                messages=data_messages, temperature=0, max_length=MAX_CONTENT_LENGTH)
        
            calls = parse_function_call_output(data_response)

            # TODO(sirri69): THIS CAN BE ABSTRACTED IN A `update_prompt` function
            diagrams = []
            for func, param in calls:
                if func != "none":
                    if func == "generate_chart":
                        best_chart_response = param
                        user_input += f"\nUse chart type: {best_chart_response}"
                    elif func == "generate_mermaid_diagram":
                        mermaid_text, name = param.split("@,@")
                        generate_mermaid_diagram(mermaid_text=mermaid_text, filename=name+'.png')
                        diagrams.append(name)
            
            if diagrams != []:
                diagrams = "\n".join([diagram+'.png' for diagram in diagrams])

                user_input += f"""
                    We have some diagrams named:

                    {diagrams}

                    You can use them in your powerpoint."""
                
            # create the slide and append it to the deck
            slide_messages = format_simple_message_for_gpt(
                system_message=SLIDE_CREATION_PROMPT, user_message=user_input)
            slide_response = call_gpt_with_backoff(
                messages=slide_messages, temperature=0.2, max_length=MAX_CONTENT_LENGTH)
            
            slide_json = json.loads(slide_response)
            deck.append(slide_json)


        # TODO(sirri69) : Both title and filename can be generated in one call
        title_messages = format_simple_message_for_gpt(
            system_message=TITLE_GEN_SYSTEM_PROMPT, user_message=str(outline))
        title_response = call_gpt_with_backoff(messages=title_messages)
        title = title_response.replace('"', '')

        filename_message = format_simple_message_for_gpt(
            system_message=FILENAME_SYSTEM_PROMPT, user_message=title_response)
        filename_response = call_gpt_with_backoff(
            messages=filename_message, temperature=0)
        filename_response = filename_response.replace('"', '')

        ppt = PowerPointCreator(title=title, slides_content=deck)
        ppt.create(file_name=filename_response)
        
        return filename_response
                

            


