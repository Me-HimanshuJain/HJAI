import queue
import time
import threading
import numpy as np
from faster_whisper import WhisperModel

# ============================================================
# Whisper runs on CPU (int8), Ollama uses GPU separately.
# CTranslate2 v4+ on Windows silently crashes on CUDA init —
# keeping Whisper on CPU is the permanent, stable fix.
# ============================================================

# Language labels Whisper sometimes hallucinates as first word
_LANG_LABELS = {
    "English", "Hindi", "Japanese", "Chinese", "Korean",
    "French", "German", "Spanish", "Thai", "Arabic", "Russian",
}


class Transcriber:
    # ── Tunable constants ────────────────────────────────────────────────────
    # RMS below this → silence (no speech)
    SILENCE_THRESHOLD = 0.015
    # Seconds of consecutive silence before we call "person stopped speaking"
    SILENCE_TRIGGER_SEC = 1.2
    # Minimum speech samples required to attempt transcription (1 second)
    MIN_SPEECH_SAMPLES = 16000

    def __init__(self, model_size="medium"):
        print(f"Loading Whisper model '{model_size}' on CPU (permanent, stable)...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Whisper loaded successfully!")
        self.text_queue = queue.Queue()
        self.is_running = False
        self.is_paused = False        # controlled by UI pause button
        self._flush_event = threading.Event()  # set by flush() to trigger immediate transcription

    # ── Core transcription ───────────────────────────────────────────────────

    def process_audio_chunk(self, audio_data: np.ndarray):
        """Transcribe a speech segment (already silence-gated by the worker)."""
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            language=None,
            condition_on_previous_text=False,
            no_speech_threshold=0.45,
            initial_prompt="English and Hindi conversation transcript:",
        )

        text = ""
        for segment in segments:
            if segment.no_speech_prob > 0.4:
                continue
            text += segment.text + " "

        text = text.strip()

        # Strip language-label hallucinations (e.g. "English in the position...")
        words = text.split()
        if words and words[0] in _LANG_LABELS:
            words = words[1:]
            text = " ".join(words).strip()

        # Drop very short or repetitive noise segments
        if len(text) < 8 or len(set(text.lower().replace(" ", ""))) < 4:
            return

        if text:
            print(f"[Heard] {text}")
            self.text_queue.put(text)

    # ── Background worker ────────────────────────────────────────────────────

    def start_worker(self, audio_queue: queue.Queue):
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, args=(audio_queue,), daemon=True)
        self.thread.start()

    def _worker(self, audio_queue: queue.Queue):
        """
        Silence-triggered transcription:
        Accumulate audio while speech is detected.
        When silence lasts >= SILENCE_TRIGGER_SEC OR flush() is called,
        flush buffer → transcribe.
        """
        speech_buffer = []
        last_speech_time = None
        triggered = False

        while self.is_running:
            # ── Check for manual flush (Pause button pressed mid-speech) ──────
            if self._flush_event.is_set():
                self._flush_event.clear()
                if speech_buffer:
                    print("[Transcriber] Manual flush triggered (Pause)")
                    self._flush(speech_buffer)
                    speech_buffer = []
                    triggered = True
                continue

            try:
                chunk = audio_queue.get(timeout=0.1)
            except queue.Empty:
                # No audio — check if silence timeout reached
                if (speech_buffer and last_speech_time is not None
                        and not triggered
                        and not self.is_paused):
                    silence_dur = time.time() - last_speech_time
                    if silence_dur >= self.SILENCE_TRIGGER_SEC:
                        self._flush(speech_buffer)
                        speech_buffer = []
                        triggered = True
                continue
            except Exception as e:
                print(f"[Transcriber] Queue error: {e}")
                continue

            if self.is_paused:
                continue  # discard audio while paused

            try:
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if rms >= self.SILENCE_THRESHOLD:
                    # Active speech
                    speech_buffer.append(chunk)
                    last_speech_time = time.time()
                    triggered = False
                else:
                    # Silence frame — check timeout
                    if (speech_buffer and last_speech_time is not None
                            and not triggered):
                        silence_dur = time.time() - last_speech_time
                        if silence_dur >= self.SILENCE_TRIGGER_SEC:
                            self._flush(speech_buffer)
                            speech_buffer = []
                            triggered = True
            except Exception as e:
                print(f"[Transcriber] Processing error: {e}")
                speech_buffer.clear()

    def _flush(self, speech_buffer: list):
        """Concatenate buffer and transcribe if long enough."""
        try:
            audio_data = np.concatenate(speech_buffer)
            if len(audio_data) >= self.MIN_SPEECH_SAMPLES:
                self.process_audio_chunk(audio_data)
        except Exception as e:
            print(f"[Transcriber] Flush error: {e}")

    # ── Public API ───────────────────────────────────────────────────────────

    def flush(self):
        """Called by UI Pause button to immediately transcribe buffered speech."""
        self._flush_event.set()

    def reset(self):
        """Clear the text queue (called by Reset button)."""
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                break

    def get_latest_text(self):
        text = []
        while not self.text_queue.empty():
            text.append(self.text_queue.get())
        return " ".join(text)

    def stop(self):
        self.is_running = False
        if hasattr(self, "thread"):
            self.thread.join(timeout=2.0)
