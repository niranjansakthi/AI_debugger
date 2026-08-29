import os
from dotenv import load_dotenv

from huggingface_hub import InferenceClient

load_dotenv()

class CodeEmbedder:

    def __init__(
        self,
        model_name: str | None = None,
    ):
        token = os.getenv("HF_TOKEN")

        if not token:
            raise ValueError(
                "HF_TOKEN environment variable is not configured"
            )

        self.model_name = (
            model_name
            or os.getenv(
                "HF_EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            )
        )

        self.client = InferenceClient(
            provider="hf-inference",
            api_key=token,
        )

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        embeddings = self.client.feature_extraction(
            texts,
            model=self.model_name,
            normalize=True,
        )

        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return embeddings