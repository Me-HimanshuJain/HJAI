import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os

logger = logging.getLogger(__name__)

class Distributor:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = "llama3:8b" # Assuming standard Llama 3 8B model locally
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")

    def generate_meeting_recap(self, transcript: str, metadata: dict) -> dict:
        prompt = f"""
        You are HJAI Meeting Assistant. Analyze the following meeting transcript.
        Meeting Context: {json.dumps(metadata)}
        
        Transcript:
        {transcript}
        
        Respond ONLY with a valid JSON object matching this structure:
        {{
            "summary": "High level summary",
            "action_items": [
                {{"assignee": "Name or Unassigned", "task": "Description"}}
            ]
        }}
        """
        
        logger.info(f"Generating recap with {self.model_name}")
        try:
            response = requests.post(f"{self.ollama_host}/api/generate", json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            })
            
            response.raise_for_status()
            result_text = response.json().get("response", "")
            
            # Extract JSON block
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = result_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("LLM did not return JSON")
                
        except Exception as e:
            logger.error(f"Failed to generate recap: {e}")
            return {"summary": "Failed to generate recap.", "action_items": []}

    def send_recap_email(self, recipients: list, recap: dict, metadata: dict):
        if not self.smtp_user or not self.smtp_pass:
            logger.warning("SMTP credentials not set. Cannot send email.")
            return
            
        subject = f"Meeting Recap: {metadata.get('title', 'Unknown Meeting')}"
        
        body = f"Summary:\n{recap.get('summary', '')}\n\nAction Items:\n"
        for item in recap.get("action_items", []):
            body += f"- {item.get('assignee', 'Unassigned')}: {item.get('task', '')}\n"

        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            text = msg.as_string()
            server.sendmail(self.smtp_user, recipients, text)
            server.quit()
            logger.info("Recap email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
