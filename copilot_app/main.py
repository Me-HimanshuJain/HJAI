import sys
import ctypes
import traceback

# Force UTF-8 output on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ── STEP 1: Initialize ALL engines on the MAIN thread, before Qt starts ──────
print("Initializing audio capture...")
from audio_streamer import AudioStreamer
audio = AudioStreamer()

print("Loading Whisper AI model (may take ~30 sec first time)...")
from transcriber import Transcriber
transcriber = Transcriber()   # uses 'medium' by default

print("Connecting to Ollama AI engine...")
from ai_engine import AIEngine
ai = AIEngine()

print("Starting background workers...")
audio.start()
transcriber.start_worker(audio.audio_queue)
ai.start_worker(transcriber.text_queue)

print("All engines ready! Launching UI...")

# ── STEP 2: Only NOW start Qt ─────────────────────────────────────────────────
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QVBoxLayout, QHBoxLayout, QWidget,
    QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

WDA_EXCLUDEFROMCAPTURE = 0x00000011

# ── Shared stylesheet helpers ─────────────────────────────────────────────────
_BTN_BASE = (
    "QPushButton {"
    "  font-size: 11px; font-weight: bold;"
    "  border-radius: 6px; padding: 5px 12px;"
    "  border: none; cursor: pointer;"
    "}"
)
_BTN_CYAN = _BTN_BASE + (
    "QPushButton { background: #00FFCC; color: #0d0d1a; }"
    "QPushButton:hover { background: #00ddb0; }"
    "QPushButton:pressed { background: #00bfa0; }"
)
_BTN_RED = _BTN_BASE + (
    "QPushButton { background: #ff4466; color: #fff; }"
    "QPushButton:hover { background: #e03355; }"
    "QPushButton:pressed { background: #c02244; }"
)
_BTN_ORANGE = _BTN_BASE + (
    "QPushButton { background: #ff8800; color: #fff; }"
    "QPushButton:hover { background: #e07700; }"
    "QPushButton:pressed { background: #c06600; }"
)


class CopilotWindow(QMainWindow):
    def __init__(self, audio, transcriber, ai):
        super().__init__()
        self._audio = audio
        self._transcriber = transcriber
        self._ai = ai
        self._paused = False
        self._build_ui()
        self._hide_from_capture()

        # Poll every 400ms for transcripts and answers
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._refresh)
        self.ui_timer.start(400)

    # ── UI builder ────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("HJAI Copilot")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(500, 400)
        self.move(80, 80)

        root = QWidget()
        root.setStyleSheet("background-color: #0d0d1a;")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # ── Header row ────────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        header = QLabel("⚡ HJAI Copilot  |  Invisible to Screen Share")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FFCC;")
        header_row.addWidget(header, stretch=1)

        # Pause / Resume button
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet(_BTN_CYAN)
        self.pause_btn.setFixedWidth(90)
        self.pause_btn.clicked.connect(self._toggle_pause)
        header_row.addWidget(self.pause_btn)

        # Reset button
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet(_BTN_ORANGE)
        reset_btn.setFixedWidth(80)
        reset_btn.clicked.connect(self._reset)
        header_row.addWidget(reset_btn)

        layout.addLayout(header_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep1)

        # ── Status label ──────────────────────────────────────────────────────
        self.status_label = QLabel("🎧 Listening to system audio...")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #555;")
        layout.addWidget(self.status_label)

        # ── HEARD section ─────────────────────────────────────────────────────
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
        self.transcript_label.setMaximumHeight(90)
        layout.addWidget(self.transcript_label)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep2)

        # ── ANSWER section ────────────────────────────────────────────────────
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

    # ── Button handlers ───────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._paused = not self._paused
        self._transcriber.is_paused = self._paused
        if self._paused:
            self.pause_btn.setText("▶ Resume")
            self.pause_btn.setStyleSheet(_BTN_RED)
            self.status_label.setText("⏸ Paused — click Resume to continue listening")
            self.status_label.setStyleSheet("color: #ff4466;")
        else:
            self.pause_btn.setText("⏸ Pause")
            self.pause_btn.setStyleSheet(_BTN_CYAN)
            self.status_label.setText("🎧 Listening to system audio...")
            self.status_label.setStyleSheet("color: #555;")

    def _reset(self):
        """Clear all display state and AI buffers."""
        self._transcriber.reset()
        self._ai.reset()
        self.transcript_label.setText("Listening for speech...")
        self.answer_label.setStyleSheet(
            "color: #e8e8ff; background: #131325; border-radius: 6px; padding: 10px;"
            "border-left: 3px solid #00FFCC;"
        )
        self.answer_label.setText("Answer will appear here after someone speaks...")
        if not self._paused:
            self.status_label.setText("🎧 Listening to system audio...")

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _refresh(self):
        # Update transcript display
        new_transcript = self._ai.get_latest_transcript()
        if new_transcript:
            current = self.transcript_label.text()
            if current in ("Listening for speech...", ""):
                current = ""
            combined = (current + " " + new_transcript).strip()
            if len(combined) > 220:
                combined = "…" + combined[-220:]
            self.transcript_label.setText(combined)

        # Show Thinking… while Ollama is generating
        if self._ai.is_thinking:
            if "Thinking" not in self.answer_label.text():
                self.answer_label.setStyleSheet(
                    "color: #aaa; background: #131325; border-radius: 6px; padding: 10px;"
                    "border-left: 3px solid #ffaa00;"
                )
                self.answer_label.setText("⏳ Thinking…")
            if not self._paused:
                self.status_label.setText("🤖 Generating answer…")
                self.status_label.setStyleSheet("color: #ffaa00;")
        else:
            answer = self._ai.get_latest_answer()
            if answer:
                self.answer_label.setStyleSheet(
                    "color: #e8e8ff; background: #131325; border-radius: 6px; padding: 10px;"
                    "border-left: 3px solid #00FFCC;"
                )
                self.answer_label.setText(answer)
                if not self._paused:
                    self.status_label.setText("🎧 Listening to system audio...")
                    self.status_label.setStyleSheet("color: #555;")

    # ── Shutdown ──────────────────────────────────────────────────────────────

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
