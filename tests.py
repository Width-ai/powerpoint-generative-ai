from dotenv import load_dotenv
import os
load_dotenv()


from powerpoint_generative_ai.ppt_generator import PowerPointGenerator

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

USER_TEXTS = [
"""create a six slide powerpoint about the growing obesity rate and its effect on health insurance premiums. here is some data for a chart:
x axis: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
US: 5%, 10%, 15%, 20%, 25%, 30%, 35%, 40%
UK: 3%, 6%, 9%, 12%, 15%, 18%, 21%, 24%
RU: 2%, 4%, 6%, 8%, 10%, 12%, 14%, 16%
FR: 7%, 14%, 21%, 28%, 35%, 42%, 49%, 56%
IT: 1%, 2%, 3%, 4%, 5%, 6%, 7%, 8%""",
]



def generate_ppt():
    ppt_generator = PowerPointGenerator(OPENAI_API_KEY)
    powerpoint_files = [ppt_generator.create_powerpoint(user_input=user_text) for user_text in USER_TEXTS]
    


if __name__ == "__main__":
    generate_ppt()