import re

from rank_bm25 import BM25Okapi

from repository.models.code_chunk import CodeChunk


class BM25Retriever:

    def __init__(
        self,
        chunks: list[CodeChunk],
    ):
        self.chunks = chunks

        self.tokenized_documents = [
            self._tokenize(
                self._document_text(chunk)
            )
            for chunk in chunks
        ]

        if self.tokenized_documents:
            self.bm25 = BM25Okapi(
                self.tokenized_documents
            )
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[CodeChunk]:

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        top_k = min(top_k, len(self.chunks))

        if top_k == 0:
            return []

        query_tokens = self._tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]

        return [
            self.chunks[index]
            for index in ranked_indices
        ]

    def _document_text(
        self,
        chunk: CodeChunk,
    ) -> str:

        return " ".join(
            [
                chunk.file_path,
                chunk.chunk_type,
                chunk.name or "",
                chunk.content,
            ]
        )

    def _tokenize(self, text: str) -> list[str]:

        return re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*",
            text.lower(),
        )