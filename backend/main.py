from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api import chat, memory, documents, vision, voice, agents

app = FastAPI(
    title="HJAI API",
    description="Backend API for the HJAI Assistant Platform",
    version="1.0.0"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(documents.router, prefix="/api/documents")
app.include_router(vision.router, prefix="/api/vision")
app.include_router(voice.router, prefix="/api/voice")
app.include_router(agents.router, prefix="/api/agents")

@app.get("/")
def read_root():
    return {"message": "Welcome to HJAI API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
