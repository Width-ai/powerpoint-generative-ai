import openai
import pinecone
from typing import List, Callable
from .ppt.ppt_loader import PPTLoader
from .utils.pinecone_utils import index_data, search_pinecone_index

class PowerPointAnalyzer:
    """Analyze PPT files."""
    def __init__(self, openai_key: str, pinecone_key: str, pinecone_index: str, pinecone_env: str, custom_embeddings_function: Callable[[List], List] = None):
        """
        Initialize with api_keys and other vars. Also takes in an optional custom
        embeddings function that can be used, function signature should be as follows:

        def custom_embeddings_funciton(texts: List[str]) -> List[List]:
            # call your embeddings service of choice for each text in the input list
            # return a List of lists of embedded vectors
        """
        openai.api_key = openai_key
        pinecone.init(api_key=pinecone_key, environment=pinecone_env)
        self.pinecone_index = pinecone.Index(index_name=pinecone_index)
        self.custom_embeddings_function = custom_embeddings_function


    def load(self, file_paths: List[str]):
        """Load from file paths and index the data into pinecone"""
        # load all the documents from the given filepaths
        docs = []
        for file_path in file_paths:
            docs.extend(PPTLoader(file_path).load())
        
        # insert all the data into pinecone to be queried later
        if self.custom_embeddings_function:
            index_data(index=self.pinecone_index, documents=docs, get_embeddings=self.custom_embeddings_function)
        else:
            index_data(index=self.pinecone_index, documents=docs)


    def search_for_relevant_slides(self, query: str, num_results: int = 5, threshold: float = 0.8) -> List[str]:
        """Search on the pinecone index for relevant slides based on the user query"""
        return search_pinecone_index(
            index=self.pinecone_index,
            query=query,
            num_results=num_results,
            threshold=threshold
        )