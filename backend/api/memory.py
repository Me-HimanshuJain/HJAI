from fastapi import APIRouter, Depends
from pydantic import BaseModel
from memory.memory_manager import MemoryManager
from sqlalchemy.orm import Session
from database.database import get_db

router = APIRouter()

class MemoryRequest(BaseModel):
    user_id: str
    memory_text: str

@router.post("/memory")
def save_memory(request: MemoryRequest, db: Session = Depends(get_db)):
    """Manually save a memory for the user."""
    memory_id = MemoryManager.store_memory(user_id=request.user_id, memory_text=request.memory_text, db=db)
    return {"status": "success", "memory_id": memory_id}

@router.get("/memory/{user_id}")
def get_memories(user_id: str, query: str, limit: int = 5):
    """Retrieve memories for a user based on a query."""
    memories = MemoryManager.retrieve_relevant_memories(user_id=user_id, query=query, n_results=limit)
    return {"memories": memories}
