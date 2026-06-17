from sentence_transformers import SentenceTransformer

# Load the model once
# all-MiniLM-L6-v2 is lightweight and maps sentences to a 384 dimensional dense vector space.
model = SentenceTransformer('all-MiniLM-L6-v2')

class EmbeddingService:
    @staticmethod
    def generate_embedding(text: str) -> list[float]:
        """Generates a dense vector embedding for the given text."""
        embedding = model.encode(text)
        return embedding.tolist()
    
    @staticmethod
    def generate_embeddings(texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a list of texts."""
        embeddings = model.encode(texts)
        return embeddings.tolist()
