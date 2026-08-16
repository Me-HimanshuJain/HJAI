from worker import celery_app
from services.llm_service import LLMService
import asyncio

@celery_app.task
def execute_coder_agent(requirements: str):
    """
    Coder Agent: Generates code based on requirements.
    """
    system_prompt = "You are the Coder Agent. Your job is to write clean, secure, and efficient code based on the provided requirements. Return only the code and necessary comments."

    try:
        response = asyncio.run(LLMService.generate_response(
            prompt=requirements,
            system=system_prompt
        ))
        return {"status": "success", "agent": "coder", "code": response}
    except Exception as e:
        return {"status": "error", "agent": "coder", "error": str(e)}
