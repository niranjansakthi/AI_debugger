from pydantic import BaseModel, Field
from typing import Type

from repository.ai.context_builder import RepositoryContextBuilder


class SearchCodeInput(BaseModel):
    query: str = Field(
        ...,
        description="The natural language query to search the codebase for (e.g., 'authentication logic', 'user model')."
    )


class SearchCodeTool:
    """Searches the repository for code matching a natural language query."""
    
    name = "search_code"
    description = "Use this tool to search the codebase for specific functions, classes, or logic."
    args_schema: Type[BaseModel] = SearchCodeInput

    def __init__(
        self, 
        retriever, 
        context_builder: RepositoryContextBuilder
    ):
        self.retriever = retriever
        self.context_builder = context_builder

    def execute(self, query: str, top_k: int = 5) -> str:
        chunks = self.retriever.search(query, top_k=top_k)
        
        if not chunks:
            return f"No relevant code found for query: '{query}'"
            
        context_items = self.context_builder.build(chunks)
        formatted_context = self.context_builder.format(context_items)
        
        return formatted_context
