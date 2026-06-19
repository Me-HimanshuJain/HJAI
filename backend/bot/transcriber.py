import os
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class LocalTranscriber:
    def __init__(self, model_size="base"):
        logger.info(f"Loading faster-whisper model: {model_size}")
        # Use compute_type="int8" to save memory if running on CPU/limited GPU
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
    def transcribe_audio_file(self, audio_path: str):
        logger.info(f"Transcribing {audio_path}")
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        full_text = ""
        for segment in segments:
            logger.debug("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            full_text += segment.text + "\n"
            
        return full_text.strip()
