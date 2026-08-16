from worker import celery_app
from services.llm_service import LLMService
import asyncio

@celery_app.task
def execute_reviewer_agent(task_data: str):
    """
    Reviewer Agent: Verifies code or tasks for correctness and completeness.
    """
    system_prompt = "You are the Reviewer Agent. Your job is to review the provided output against the original requirements and point out any bugs, security issues, or missing features. If it looks good, approve it."

    try:
        response = asyncio.run(LLMService.generate_response(
            prompt=task_data,
            system=system_prompt
        ))
        return {"status": "success", "agent": "reviewer", "review": response}
    except Exception as e:
        return {"status": "error", "agent": "reviewer", "error": str(e)}
