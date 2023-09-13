from dotenv import load_dotenv
import os
load_dotenv()


from powerpoint_generative_ai.ppt_generator import PowerPointGenerator

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

USER_TEXTS = [
"""create a six slide powerpoint about the growing obesity rate and its effect on health insurance premiums.


Also add a diagram about biology of fat cells.
""",
]



def generate_ppt():
    ppt_generator = PowerPointGenerator(OPENAI_API_KEY)
    powerpoint_files = [ppt_generator.create_powerpoint(user_input=user_text) for user_text in USER_TEXTS]
    


if __name__ == "__main__":
    generate_ppt()