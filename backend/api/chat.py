from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from services.llm_service import LLMService
from memory.memory_manager import MemoryManager
from sqlalchemy.orm import Session
from database.database import get_db
import asyncio

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Retrieve relevant memories for the user
    memories = MemoryManager.retrieve_relevant_memories(user_id=request.user_id, query=request.message)
    
    # 2. Extract new memory from the message (runs asynchronously)
    # In a real production system, this could be offloaded to Celery.
    memory_extraction = await MemoryManager.extract_memory_from_message(request.message)
    if memory_extraction.get("is_memory") and memory_extraction.get("fact"):
        MemoryManager.store_memory(user_id=request.user_id, memory_text=memory_extraction["fact"], db=db)
    
    # 3. Construct the prompt with context
    system_prompt = """You are HJAI, a highly capable, all-purpose AI assistant. You can help with ANYTHING — \
general knowledge, science, history, geography, math, philosophy, creative writing, coding, cooking, travel, \
health, sports, entertainment, news, and much more. You NEVER refuse to answer a question by saying it is \
unrelated to a previous topic. Every question deserves a direct, accurate, and helpful answer.

IMPORTANT RULES:
- Always answer the user's CURRENT question directly and completely.
- Do NOT redirect the user back to a previous topic or say things like "since you were asking about X earlier..."
- Do NOT assume the user only wants help with one specific domain (e.g., coding).
- If the user's memories below are relevant, use them as helpful context. If they are NOT relevant to the current question, IGNORE them entirely.
- Be concise, friendly, and accurate. Cite sources or give examples when helpful."""

    if memories:
        system_prompt += "\n\n[User Context — use only if relevant to the current question]:\n"
        for mem in memories:
            system_prompt += f"- {mem}\n"
            
    # 4. Generate streaming response
    async def response_generator():
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        async for chunk in LLMService.chat_stream(messages=messages):
            yield chunk

    return StreamingResponse(response_generator(), media_type="text/plain")
