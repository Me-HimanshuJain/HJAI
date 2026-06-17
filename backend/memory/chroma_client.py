import os
import chromadb
from chromadb.config import Settings

CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", 8000))

# Initialize ChromaDB client
chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, settings=Settings(allow_reset=True))

class ChromaService:
    @staticmethod
    def get_or_create_collection(collection_name: str):
        """Gets or creates a collection in ChromaDB."""
        return chroma_client.get_or_create_collection(name=collection_name)

    @staticmethod
    def add_documents(collection_name: str, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] = None):
        """Adds documents with their embeddings to a specific collection."""
        collection = ChromaService.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    @staticmethod
    def query_collection(collection_name: str, query_embeddings: list[list[float]], n_results: int = 5):
        """Queries a collection by vector similarity."""
        collection = ChromaService.get_or_create_collection(collection_name)
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
        return results
