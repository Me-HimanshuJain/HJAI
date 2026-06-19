import os
import sys
import queue
import time
import threading
import numpy as np
from faster_whisper import WhisperModel

# ============================================================
# PERMANENT FIX: Whisper runs on CPU, Ollama runs on GPU.
#
# Root Cause: CTranslate2 v4+ on Windows silently aborts at the
# C++ level when initializing CUDA, completely bypassing Python's
# try/except. This is a known upstream bug with CUDA 12.x drivers.
#
# Solution: The "base" Whisper model (74MB) transcribes in
# near-real-time on CPU. Ollama (the heavy AI model) uses the
# GPU via its own separate CUDA runtime. Best of both worlds.
# ============================================================

class Transcriber:
    def __init__(self, model_size="base"):
        print(f"Loading Whisper model '{model_size}' on CPU (permanent, stable)...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Whisper loaded successfully!")
        self.text_queue = queue.Queue()
        self.is_running = False

    # Minimum RMS amplitude to consider audio as speech (not silence)
    SILENCE_THRESHOLD = 0.01

    def process_audio_chunk(self, audio_data: np.ndarray):
        """Transcribe audio only if speech is actually detected (VAD gate)."""
        # ── Voice Activity Detection ──────────────────────────────────────────
        rms = float(np.sqrt(np.mean(audio_data ** 2)))
        if rms < self.SILENCE_THRESHOLD:
            return  # Skip silent chunks — prevents Whisper hallucinations

        # ── Transcribe with anti-hallucination settings ───────────────────────
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            # No language lock — Whisper auto-detects English & Hindi per chunk
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            initial_prompt="Meeting transcript:",
        )

        text = ""
        for segment in segments:
            if segment.no_speech_prob > 0.6:
                continue
            text += segment.text + " "

        text = text.strip()
        if text:
            print(f"[Heard] {text}")
            self.text_queue.put(text)

    def start_worker(self, audio_queue: queue.Queue):
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, args=(audio_queue,))
        self.thread.daemon = True
        self.thread.start()

    def _worker(self, audio_queue: queue.Queue):
        buffer = []
        last_process_time = time.time()

        while self.is_running:
            try:
                audio_chunk = audio_queue.get(timeout=0.1)
                buffer.append(audio_chunk)
            except queue.Empty:
                pass

            # Process buffer every 1 second for low-latency transcription
            if time.time() - last_process_time > 1.0 and len(buffer) > 0:
                audio_data = np.concatenate(buffer)
                if len(audio_data) > 16000:  # At least 1 second at 16kHz
                    self.process_audio_chunk(audio_data)
                buffer = []
                last_process_time = time.time()

    def get_latest_text(self):
        text = []
        while not self.text_queue.empty():
            text.append(self.text_queue.get())
        return " ".join(text)

    def stop(self):
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2.0)
