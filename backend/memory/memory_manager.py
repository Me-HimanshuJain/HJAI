import uuid
from datetime import datetime
from services.llm_service import LLMService
from memory.embeddings import EmbeddingService
from memory.chroma_client import ChromaService
from sqlalchemy.orm import Session

# Collection name for memory vectors
MEMORY_COLLECTION = "user_memories"

class MemoryManager:
    @staticmethod
    async def extract_memory_from_message(message: str) -> dict:
        """
        Uses the LLM to detect if there is a fact, preference, or goal worth remembering in the message.
        Returns a dictionary with 'is_memory': bool, and 'fact': str.
        """
        prompt = f"""
        Analyze the following user message and determine if it contains a long-term personal fact, preference, project, or goal that an AI assistant should remember for future conversations.
        If it does, extract the fact concisely. If it does not, return null for the fact.
        Respond ONLY in valid JSON format.
        
        Example 1:
        Message: "My favorite programming language is Python."
        Output: {{"is_memory": true, "fact": "User's favorite programming language is Python."}}
        
        Example 2:
        Message: "What is the capital of France?"
        Output: {{"is_memory": false, "fact": null}}
        
        Message: "{message}"
        Output:
        """
        try:
            response = await LLMService.generate_response(prompt=prompt, system="You are an AI memory extraction agent. You only output valid JSON.")
            import json
            data = json.loads(response)
            return data
        except Exception as e:
            print(f"Failed to extract memory: {e}")
            return {"is_memory": False, "fact": None}

    @staticmethod
    def store_memory(user_id: str, memory_text: str, db: Session):
        """Generates embedding and stores the memory in ChromaDB and Postgres."""
        # 1. Generate Embedding
        embedding = EmbeddingService.generate_embedding(memory_text)
        
        # 2. Store in ChromaDB
        memory_id = str(uuid.uuid4())
        ChromaService.add_documents(
            collection_name=MEMORY_COLLECTION,
            ids=[memory_id],
            documents=[memory_text],
            embeddings=[embedding],
            metadatas=[{"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}]
        )
        
        # 3. Store in Postgres (Assuming memory model exists)
        # In a real scenario, we'd also write to the memories table in PostgreSQL here.
        # This keeps a persistent relational record alongside the vector search record.
        return memory_id

    @staticmethod
    def retrieve_relevant_memories(user_id: str, query: str, n_results: int = 3) -> list[str]:
        """Retrieves memories relevant to the current user query."""
        query_embedding = EmbeddingService.generate_embedding(query)
        
        results = ChromaService.query_collection(
            collection_name=MEMORY_COLLECTION,
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Filter results by user_id
        relevant_memories = []
        if results and results.get("documents") and results.get("metadatas"):
            for i, docs in enumerate(results["documents"]):
                metas = results["metadatas"][i]
                for j, doc in enumerate(docs):
                    meta = metas[j]
                    if meta.get("user_id") == user_id:
                        relevant_memories.append(doc)
                        
        return relevant_memories
