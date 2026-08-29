from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.models.code_chunk import CodeChunk


class CodeRetriever:

    def __init__(
        self,
        embedder: CodeEmbedder,
        vector_store: CodeVectorStore,
    ):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[CodeChunk]:

        query_embedding = self.embedder.embed(
            [question]
        )[0]

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )