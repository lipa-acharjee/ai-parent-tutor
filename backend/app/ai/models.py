
from typing import Protocol

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings


class AIProvider(Protocol):
    def chat(self, prompt: str):
        ...


class GroqProvider:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            temperature=0.2,
        )

    def chat(self, prompt: str):
        return self.llm.invoke(prompt)


class EmbeddingProvider:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = HuggingFaceEmbeddings(
                model_name=settings.embedding_model
            )

        return self._model

    def embed_documents(self, texts):
        return self.model.embed_documents(texts)

    def embed_query(self, text):
        return self.model.embed_query(text)


# Groq client is lightweight enough to initialize at startup.
llm_provider = GroqProvider()

# IMPORTANT:
# The HuggingFace embedding model is NOT loaded at startup.
# It will only be loaded if embeddings are actually requested.
embedding_provider = EmbeddingProvider()
