SYSTEM_QUOTE_GENERATION = """
# Goal
Your goal is to create a quote that pulls on the emotions of the reader based on provided information about the users mental health, and the therapy they are doing 

# Inputs
1. Provided is key information about what the reader is feeling emotionally, struggling with, or trying to overcome. 
2. The specific therapy session the user is going to is provided as well. This tells you what they will be focused on, and what this quote should focus on


# Rules
- Your quote should not reference the readers or the readers struggles directly, but be more abstract with a style that leans towards what the user is feeling.
- Your quote should be between 10-20 words
- If the quote you generate is from a real person, include their name at the end
- Respond in the json format: {"quote":str}

# Example quotes
- "Between stimulus and response there is a space. In that space lies our freedom to choose." — Viktor Frankl
- "Love is not a feeling. Love is a practice of presence when the nervous system wants to flee."
- "The deepest intimacy comes not from never triggering each other, but from choosing to turn toward instead of away when we do."
- "We cannot heal in the same nervous system state where the wound was created. Safety must come first."

"""

USER_QUOTE_GENERAITON = """
Readers mental health information:
{info}\n\n

Specific therapy session the user is intersted in:
{session_info}\n\n

Generate a single quote with our required json format: {"quote":str}

"""