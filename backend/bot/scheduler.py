from celery import Celery
from celery.schedules import crontab
from bot.calendar_client import CalendarClient
from bot.browser_bot import launch_bot
from bot.audio_capture import AudioCapture
from bot.transcriber import LocalTranscriber
from bot.distributor import Distributor
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

celery_app = Celery("bot_tasks", broker="redis://redis:6379/0")

# Schedule the daily meeting fetch at 6:00 AM
celery_app.conf.beat_schedule = {
    'fetch-daily-meetings': {
        'task': 'bot.scheduler.fetch_daily_meetings',
        'schedule': crontab(hour=6, minute=0),
    },
}
celery_app.conf.timezone = 'UTC'

@celery_app.task
def fetch_daily_meetings():
    logger.info("Running daily meeting fetch...")
    client = CalendarClient()
    meetings = client.get_todays_meetings()
    
    for meeting in meetings:
        start_time_str = meeting['start_time']
        # Parse ISO 8601 string
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        
        # Schedule the bot to join 1 minute before the meeting
        join_time = start_time - timedelta(minutes=1)
        
        logger.info(f"Scheduling bot to join {meeting['title']} at {join_time}")
        
        # Delay the task execution until the join_time
        join_meeting_task.apply_async(args=[meeting['link'], meeting['title']], eta=join_time)

@celery_app.task
def join_meeting_task(meeting_url: str, title: str):
    logger.info(f"Bot is waking up to join meeting: {title}")
    
    meeting_id = meeting_url.split('/')[-1].split('?')[0] # Basic ID extraction
    
    # 1. Start Audio Capture (in background)
    audio = AudioCapture()
    audio_file = audio.start_recording(meeting_id)
    
    try:
        # 2. Join Meeting via Playwright (Blocking until meeting ends)
        asyncio.run(launch_bot(meeting_url))
    except Exception as e:
        logger.error(f"Error during meeting: {e}")
    finally:
        # 3. Stop Audio Capture
        audio.stop_recording()
        
        # 4. Process Transcription
        transcriber = LocalTranscriber()
        transcript = transcriber.transcribe_audio_file(audio_file)
        
        # 5. Distribute Summary
        distributor = Distributor()
        recap = distributor.generate_meeting_recap(transcript, {"title": title, "url": meeting_url})
        distributor.send_recap_email(["attendee@example.com"], recap, {"title": title})
