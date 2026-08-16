from worker import celery_app
from services.llm_service import LLMService
import asyncio

@celery_app.task
def execute_researcher_agent(topic: str):
    """
    Researcher Agent: Gathers information and answers specific questions.
    """
    system_prompt = "You are the Researcher Agent. Your job is to gather and summarize factual information about the provided topic."

    try:
        response = asyncio.run(LLMService.generate_response(
            prompt=topic,
            system=system_prompt
        ))
        return {"status": "success", "agent": "researcher", "research_notes": response}
    except Exception as e:
        return {"status": "error", "agent": "researcher", "error": str(e)}
