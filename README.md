# PowerPoint-Generative-AI
This library streamlines the utilization of GPT models for automatic PowerPoint content generation. It further offers a class for loading PowerPoints and performing semantic searches on slide content, enabling you to quickly pinpoint relevant information.

## Setup
```
conda create -n 'powerpoint' python=3.10
conda activate powerpoint
pip install -r requirements.txt
```

## How to use
```python
from ppt_generator import PowerPointGenerator
from ppt_analyzer import PowerPointAnalyzer


# set up two classes
ppt_gen = PowerPointGenerator(openai_key="...", model="gpt-4")
ppt_analyzer = PowerPointAnalyzer(openai_key="...", pinecone_key="...", pinecone_index="...", pinecone_env="...")


# Prompts to generate powerpoints for
USER_TEXTS = [
"""create a six slide powerpoint about the growing obesity rate and its effect on health insurance premiums. here is some data for a chart:
x axis: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
US: 5%, 10%, 15%, 20%, 25%, 30%, 35%, 40%
UK: 3%, 6%, 9%, 12%, 15%, 18%, 21%, 24%
RU: 2%, 4%, 6%, 8%, 10%, 12%, 14%, 16%
FR: 7%, 14%, 21%, 28%, 35%, 42%, 49%, 56%
IT: 1%, 2%, 3%, 4%, 5%, 6%, 7%, 8%""",
"""Create a five slide powerpoint about street racing in america, here is some data about insurance claims related to street racing in america for a bar chart:
x axis: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
insurance claims: 12, 84, 100, 103, 109, 114, 120, 127"""
]

# generate powerpoints
powerpoint_files = [ppt_gen.create_powerpoint(user_input=user_text) for user_text in USER_TEXTS]

# load powerpoints into pinecone
ppt_analyzer.load(file_paths=powerpoint_files)

# search on the slides indexed in pinecone and return the metadata metadata
relevant_slides = ppt_analyzer.search_for_relevant_slides(query="insurance rates")
```

## Custom Embeddings Function
By default, `PowerPointAnalyzer` utilizes OpenAI's `text-embedding-ada-002` embeddings. However, an optional parameter `custom_embeddings_function` allows the use of a user-defined embeddings solution in place of OpenAI's.

This function should follow the following signature:
```python

def custom_embeddings_function(texts: List[str]) -> List:
    # The function takes in a list of strings to calculate the embeddings for
    # ...
    # Return a list of lists that represent the embeddings of the input texts


# This can then be used when instantiating an analyzer class like this
ppt_analyzer = PowerPointAnalyzer(openai_key="...", pinecone_key="...", pinecone_index="...", pinecone_env="...", custom_embeddings_function=custom_embeddings_function)
```


## Cleaning up index
```python
ppt_analyzer.pinecone_index.delete(delete_all=True)
ppt_analyzer.pinecone_index.describe_index_stats()
```
