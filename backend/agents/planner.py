from worker import celery_app
from services.llm_service import LLMService
import asyncio
import json

@celery_app.task
def execute_planner_agent(task_description: str):
    """
    Planner Agent: Decomposes a high-level task into manageable steps.
    """
    system_prompt = "You are the Planner Agent. Decompose the user's task into a detailed step-by-step plan. Return ONLY valid JSON representing the steps as a list of strings."

    try:
        response = asyncio.run(LLMService.generate_response(
            prompt=task_description,
            system=system_prompt
        ))
        plan = json.loads(response)
        return {"status": "success", "agent": "planner", "plan": plan}
    except Exception as e:
        return {"status": "error", "agent": "planner", "error": str(e)}
