import whisper
import os
import uuid
# We will lazily import TTS to avoid loading models until necessary.

# Load the whisper model once
whisper_model = whisper.load_model("base")

class VoiceService:
    @staticmethod
    def transcribe_audio(file_path: str) -> str:
        """Transcribes audio to text using Whisper."""
        try:
            result = whisper_model.transcribe(file_path)
            return result["text"].strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    @staticmethod
    def synthesize_speech(text: str, output_path: str):
        """Synthesizes text to speech using Coqui TTS."""
        try:
            from TTS.api import TTS
            # Use a lightweight TTS model, tts_models/en/vctk/vits is popular but requires agreeing to terms.
            # We will use the default generic fast model.
            tts = TTS("tts_models/en/ljspeech/fast_pitch")
            tts.tts_to_file(text=text, file_path=output_path)
            return output_path
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
