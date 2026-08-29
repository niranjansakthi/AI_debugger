import chromadb

from repository.models.code_chunk import CodeChunk


class CodeVectorStore:

    def __init__(
        self,
        collection_name: str = "repository_code",
        persist_path: str = "./chroma_db",
    ):
        self.client = chromadb.PersistentClient(
            path=persist_path
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _chunk_id(self, chunk: CodeChunk) -> str:
        return f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}"

    def add(
        self,
        embeddings: list[list[float]],
        chunks: list[CodeChunk],
    ) -> None:

        if not chunks:
            return

        if len(embeddings) != len(chunks):
            raise ValueError(f"Embeddings length ({len(embeddings)}) must match chunks length ({len(chunks)})")

        ids = [
            self._chunk_id(chunk)
            for chunk in chunks
        ]

        documents = [
            chunk.content
            for chunk in chunks
        ]

        metadatas = [
            {
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name or "",
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[CodeChunk]:

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        chunks = []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        for document, metadata in zip(
            documents,
            metadatas,
        ):
            chunks.append(
                CodeChunk(
                    content=document,
                    file_path=metadata["file_path"],
                    chunk_type=metadata["chunk_type"],
                    name=metadata["name"] or None,
                    start_line=int(metadata["start_line"]),
                    end_line=int(metadata["end_line"]),
                )
            )

        return chunks