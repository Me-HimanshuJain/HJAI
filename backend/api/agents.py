from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json

# Import the celery tasks
from agents.planner import execute_planner_agent
from agents.researcher import execute_researcher_agent
from agents.coder import execute_coder_agent
from agents.reviewer import execute_reviewer_agent
from worker import celery_app
from celery.result import AsyncResult

router = APIRouter()

class TaskRequest(BaseModel):
    task_type: str  # "planner", "researcher", "coder", "reviewer"
    prompt: str

@router.post("/task")
async def create_agent_task(request: TaskRequest):
    """
    Dispatches a task to the specified agent via Celery.
    Returns a task ID that can be used to poll for the result.
    """
    task_type = request.task_type.lower()
    
    if task_type == "planner":
        task = execute_planner_agent.delay(request.prompt)
    elif task_type == "researcher":
        task = execute_researcher_agent.delay(request.prompt)
    elif task_type == "coder":
        task = execute_coder_agent.delay(request.prompt)
    elif task_type == "reviewer":
        task = execute_reviewer_agent.delay(request.prompt)
    else:
        raise HTTPException(status_code=400, detail="Invalid task_type. Must be planner, researcher, coder, or reviewer.")
        
    return {"task_id": task.id, "status": "Task dispatched to Celery background worker."}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status and result of a background Celery task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.ready():
        response["result"] = task_result.result
        
    return response
