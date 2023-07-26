import openai
import pinecone
from typing import List
from ppt.ppt_loader import PPTLoader
from utils.pinecone_utils import index_data, search_pinecone_index

class PowerPointAnalyzer:
    """Analyze PPT files."""
    def __init__(self, openai_key: str, pinecone_key: str, pinecone_index: str, pinecone_env: str):
        """Initialize with api_keys and other vars"""
        openai.api_key = openai_key
        pinecone.init(api_key=pinecone_key, environment=pinecone_env)
        self.pinecone_index = pinecone.Index(index_name=pinecone_index)


    def load(self, file_paths: List[str]):
        """Load from file paths and index the data into pinecone"""
        # load all the documents from the given filepaths
        docs = []
        for file_path in file_paths:
            docs.extend(PPTLoader(file_path).load())
        
        # insert all the data into pinecone to be queried later
        index_data(index=self.pinecone_index, documents=docs)


    def search_for_relevant_slides(self, query: str, num_results: int = 5, threshold: float = 0.8) -> List[str]:
        """Search on the pinecone index for relevant slides based on the user query"""
        return search_pinecone_index(
            index=self.pinecone_index,
            query=query,
            num_results=num_results,
            threshold=threshold
        )