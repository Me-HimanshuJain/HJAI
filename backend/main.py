from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from api import chat, memory, agents, auth
from database.database import init_db

app = FastAPI(
    title="HJAI API",
    description="Backend API for the HJAI Assistant Platform",
    version="1.0.0"
)

# CORS Middleware setup — restricted to the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(agents.router, prefix="/api/agents")
app.include_router(auth.router, prefix="/api")

@app.on_event("startup")
def on_startup():
    """Create all database tables on startup if they don't exist."""
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to HJAI API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
