import os

# Lazy-load faster-whisper model so it doesn't block backend startup.
# faster-whisper uses ctranslate2 (CPU-optimized, ~200MB) instead of full GPU PyTorch.
_whisper_model = None

def _get_whisper_model():
    """Load the faster-whisper model only on first use (lazy loading)."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # device="cpu", compute_type="int8" — fast and works without a GPU
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


class VoiceService:
    @staticmethod
    def transcribe_audio(file_path: str) -> str:
        """Transcribes audio to text using faster-whisper (CPU)."""
        try:
            model = _get_whisper_model()
            segments, _info = model.transcribe(file_path, beam_size=5)
            text = " ".join(segment.text for segment in segments).strip()
            return text
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    @staticmethod
    def synthesize_speech(text: str, output_path: str):
        """
        Text-to-speech synthesis.
        Coqui TTS was removed due to its very large GPU PyTorch dependency.
        This is a no-op placeholder. To re-enable TTS, install a lightweight
        alternative such as `pyttsx3` (offline) or use an external TTS API.
        """
        print(f"TTS not available: '{text[:50]}...' would be spoken to {output_path}")
        return None
