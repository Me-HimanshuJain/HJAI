import sys
import ctypes
import traceback

# Force UTF-8 output on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ── STEP 1: Initialize ALL engines on the MAIN thread, before Qt starts ──────
# This avoids Windows COM conflicts when PyAudioWPatch + CTranslate2 are
# both initialized inside a QThread (which has no COM apartment set up).
print("Initializing audio capture...")
from audio_streamer import AudioStreamer
audio = AudioStreamer()

print("Loading Whisper AI model (may take ~30 sec first time)...")
from transcriber import Transcriber
transcriber = Transcriber()

print("Connecting to Ollama AI engine...")
from ai_engine import AIEngine
ai = AIEngine()

print("Starting background workers...")
audio.start()
transcriber.start_worker(audio.audio_queue)
ai.start_worker(transcriber.text_queue)

print("All engines ready! Launching UI...")

# ── STEP 2: Only NOW start Qt ─────────────────────────────────────────────────
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel,
                             QVBoxLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

WDA_EXCLUDEFROMCAPTURE = 0x00000011


class CopilotWindow(QMainWindow):
    def __init__(self, audio, transcriber, ai):
        super().__init__()
        self._audio = audio
        self._transcriber = transcriber
        self._ai = ai
        self._build_ui()
        self._hide_from_capture()

        # Poll every 500ms for transcripts and answers
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._refresh)
        self.ui_timer.start(500)

    def _build_ui(self):
        self.setWindowTitle("HJAI Copilot")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(480, 340)
        self.move(80, 80)

        root = QWidget()
        root.setStyleSheet("background-color: #0d0d1a;")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # ── Header ────────────────────────────────────────────────────────────
        header = QLabel("HJAI Copilot  |  Invisible to Screen Share")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FFCC;")
        layout.addWidget(header)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep1)

        # ── "HEARD" section ───────────────────────────────────────────────────
        heard_lbl = QLabel("HEARD")
        heard_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        heard_lbl.setStyleSheet("color: #888; letter-spacing: 2px;")
        layout.addWidget(heard_lbl)

        self.transcript_label = QLabel("Listening for speech...")
        self.transcript_label.setFont(QFont("Segoe UI", 10))
        self.transcript_label.setStyleSheet(
            "color: #aaa; background: #131325; border-radius: 6px; padding: 8px;"
        )
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setMaximumHeight(80)
        layout.addWidget(self.transcript_label)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep2)

        # ── "ANSWER" section ──────────────────────────────────────────────────
        ans_lbl = QLabel("ANSWER")
        ans_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        ans_lbl.setStyleSheet("color: #00FFCC; letter-spacing: 2px;")
        layout.addWidget(ans_lbl)

        self.answer_label = QLabel("Answer will appear here after someone speaks...")
        self.answer_label.setFont(QFont("Segoe UI", 11))
        self.answer_label.setStyleSheet(
            "color: #e8e8ff; background: #131325; border-radius: 6px; padding: 10px;"
            "border-left: 3px solid #00FFCC;"
        )
        self.answer_label.setWordWrap(True)
        self.answer_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.answer_label, stretch=1)

        self.setCentralWidget(root)

    def _hide_from_capture(self):
        hwnd = int(self.winId())
        result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if result:
            print("Window is INVISIBLE to screen share (Zoom/Meet/Teams).")
        else:
            print("WARNING: Could not hide window from capture.")

    def _refresh(self):
        # Update transcript display
        new_transcript = self._ai.get_latest_transcript()
        if new_transcript:
            current = self.transcript_label.text()
            # Keep last ~150 chars of transcript for display
            combined = (current + " " + new_transcript).strip()
            if len(combined) > 200:
                combined = "..." + combined[-200:]
            self.transcript_label.setText(combined)

        # Update answer display
        answer = self._ai.get_latest_answer()
        if answer:
            self.answer_label.setText(answer)

    def closeEvent(self, event):
        print("Shutting down...")
        try:
            self._audio.stop()
            self._transcriber.stop()
            self._ai.stop()
        except Exception as e:
            print(f"Shutdown error: {e}")
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HJAI Copilot")
    win = CopilotWindow(audio, transcriber, ai)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    sys.excepthook = lambda t, v, tb: traceback.print_exception(t, v, tb)
    main()
