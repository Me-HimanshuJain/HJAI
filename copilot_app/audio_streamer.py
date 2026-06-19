import pyaudiowpatch as pyaudio
import numpy as np
import queue
import threading


class AudioStreamer:
    """
    Captures audio from TWO sources simultaneously:
      1. WASAPI Loopback  — whatever Windows is playing (to speakers OR headset)
      2. Microphone        — the user's own voice

    This ensures full coverage whether earbuds, headphones, or speakers are used.
    """

    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.streams = []
        self.p = pyaudio.PyAudio()

    # ── Device discovery ──────────────────────────────────────────────────────

    def _find_best_loopback(self):
        """
        Finds the WASAPI loopback device that matches the current default output.
        Works even when earbuds/headset is set as the default playback device.
        """
        try:
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_out_idx = wasapi_info["defaultOutputDevice"]
            default_out = self.p.get_device_info_by_index(default_out_idx)
            default_name = default_out["name"]

            print(f"  Default output device: {default_name}")

            # Walk all loopback devices to find one matching the default output
            for loopback in self.p.get_loopback_device_info_generator():
                if default_name in loopback["name"] or loopback["name"] in default_name:
                    print(f"  Loopback matched: {loopback['name']}")
                    return loopback

            # Fallback: return the first available loopback device
            for loopback in self.p.get_loopback_device_info_generator():
                print(f"  Fallback loopback: {loopback['name']}")
                return loopback

        except OSError as e:
            print(f"  WASAPI loopback not available: {e}")
        return None

    def _find_default_microphone(self):
        """Finds the system default input (microphone) device."""
        try:
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_in_idx = wasapi_info["defaultInputDevice"]
            if default_in_idx >= 0:
                mic = self.p.get_device_info_by_index(default_in_idx)
                if mic["maxInputChannels"] > 0:
                    print(f"  Microphone: {mic['name']}")
                    return mic
        except Exception as e:
            print(f"  Microphone discovery failed: {e}")
        return None

    # ── Stream helpers ────────────────────────────────────────────────────────

    def _make_callback(self, channels, source_sample_rate):
        """Creates an audio callback that resamples to 16kHz mono float32."""
        def callback(in_data, frame_count, time_info, status):
            if not self.is_running:
                return (in_data, pyaudio.paComplete)
            try:
                audio = np.frombuffer(in_data, dtype=np.int16).copy()
                # Mix stereo/multi-channel to mono
                if channels > 1:
                    audio = audio.reshape(-1, channels)
                    audio = audio.mean(axis=1).astype(np.int16)
                # Normalize to float32 [-1, 1]
                audio_f32 = audio.astype(np.float32) / 32768.0
                # Simple decimation if sample rate is higher than 16kHz
                if source_sample_rate > self.sample_rate:
                    step = int(source_sample_rate / self.sample_rate)
                    audio_f32 = audio_f32[::step]
                self.audio_queue.put(audio_f32)
            except Exception as e:
                print(f"  Audio callback error: {e}")
            return (in_data, pyaudio.paContinue)
        return callback

    def _open_stream(self, device, is_input=True):
        """Opens a PyAudio stream for the given device."""
        try:
            channels = int(device.get("maxInputChannels" if is_input else "maxInputChannels", 1))
            channels = max(1, min(channels, 2))
            rate = int(device.get("defaultSampleRate", 16000))
            idx = int(device["index"])

            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=idx,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._make_callback(channels, rate),
            )
            stream.start_stream()
            return stream
        except Exception as e:
            print(f"  Could not open stream for {device.get('name', '?')}: {e}")
            return None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        self.is_running = True
        opened = 0

        print("Starting audio capture...")

        # 1. System audio loopback (catches meeting audio sent to earbuds/speakers)
        loopback = self._find_best_loopback()
        if loopback:
            s = self._open_stream(loopback, is_input=True)
            if s:
                self.streams.append(s)
                opened += 1
                print(f"  [OK] Loopback stream opened")
        else:
            print("  [WARN] No loopback device found — system audio will not be captured.")

        # 2. Microphone (catches the user's own speech and nearby audio)
        mic = self._find_default_microphone()
        if mic:
            s = self._open_stream(mic, is_input=True)
            if s:
                self.streams.append(s)
                opened += 1
                print(f"  [OK] Microphone stream opened")
        else:
            print("  [WARN] No microphone found.")

        if opened == 0:
            print("[ERROR] No audio sources could be opened!")
        else:
            print(f"  Capturing from {opened} audio source(s).")

    def stop(self):
        self.is_running = False
        for stream in self.streams:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        self.streams.clear()
        try:
            self.p.terminate()
        except Exception:
            pass
