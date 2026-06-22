import sys
import ctypes
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ── STEP 1: Initialize ALL engines on the MAIN thread ────────────────────────
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

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QVBoxLayout, QHBoxLayout, QWidget,
    QFrame, QPushButton, QScrollArea,
    QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

WDA_EXCLUDEFROMCAPTURE = 0x00000011

_BTN_BASE = (
    "QPushButton { font-size: 11px; font-weight: bold;"
    " border-radius: 6px; padding: 5px 12px; border: none; }"
)
_BTN_CYAN = _BTN_BASE + (
    "QPushButton { background: #00FFCC; color: #0d0d1a; }"
    "QPushButton:hover { background: #00ddb0; }"
)
_BTN_RED = _BTN_BASE + (
    "QPushButton { background: #ff4466; color: #fff; }"
    "QPushButton:hover { background: #e03355; }"
)
_BTN_ORANGE = _BTN_BASE + (
    "QPushButton { background: #ff8800; color: #fff; }"
    "QPushButton:hover { background: #e07700; }"
)


def _make_answer_card(text: str, idx: int) -> QFrame:
    """Create a styled answer card widget."""
    card = QFrame()
    card.setStyleSheet(
        "QFrame { background: #131325; border-radius: 8px;"
        " border-left: 3px solid #00FFCC; margin-bottom: 4px; }"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(2)

    num_lbl = QLabel(f"#{idx}")
    num_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
    num_lbl.setStyleSheet("color: #00FFCC; background: transparent; border: none;")
    layout.addWidget(num_lbl)

    text_lbl = QLabel(text)
    text_lbl.setFont(QFont("Segoe UI", 10))
    text_lbl.setStyleSheet("color: #e8e8ff; background: transparent; border: none;")
    text_lbl.setWordWrap(True)
    text_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.addWidget(text_lbl)
    return card


class CopilotWindow(QMainWindow):
    def __init__(self, audio, transcriber, ai):
        super().__init__()
        self._audio = audio
        self._transcriber = transcriber
        self._ai = ai
        self._paused = False
        self._answer_count = 0
        self._pending_card_label = None   # label inside current streaming card
        self._build_ui()
        self._hide_from_capture()

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._refresh)
        self.ui_timer.start(300)   # 300ms poll for snappier updates

    # ── UI builder ────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("HJAI Copilot")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool   # removes taskbar button — invisible to screen share viewers
        )
        self.resize(520, 600)
        self.move(80, 80)

        root = QWidget()
        root.setStyleSheet("background-color: #0d0d1a;")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # ── Header row ────────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header = QLabel("⚡ HJAI Copilot  |  Invisible to Screen Share")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header.setStyleSheet("color: #00FFCC;")
        header_row.addWidget(header, stretch=1)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet(_BTN_CYAN)
        self.pause_btn.setFixedWidth(90)
        self.pause_btn.clicked.connect(self._toggle_pause)
        header_row.addWidget(self.pause_btn)

        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet(_BTN_ORANGE)
        reset_btn.setFixedWidth(80)
        reset_btn.clicked.connect(self._reset)
        header_row.addWidget(reset_btn)
        layout.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep)

        # ── Status ────────────────────────────────────────────────────────────
        self.status_label = QLabel("🎧 Listening to system audio...")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #555;")
        layout.addWidget(self.status_label)

        # ── HEARD section ─────────────────────────────────────────────────────
        heard_row = QHBoxLayout()
        heard_lbl = QLabel("HEARD  (click to edit)")
        heard_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        heard_lbl.setStyleSheet("color: #888; letter-spacing: 1px;")
        heard_row.addWidget(heard_lbl, stretch=1)

        reask_btn = QPushButton("↩ Re-Ask")
        reask_btn.setStyleSheet(_BTN_CYAN)
        reask_btn.setFixedWidth(80)
        reask_btn.setToolTip("Send the edited HEARD text to the AI")
        reask_btn.clicked.connect(self._reask_from_heard)
        heard_row.addWidget(reask_btn)
        layout.addLayout(heard_row)

        # Editable transcript box — user can correct Whisper mistakes
        self.transcript_edit = QTextEdit()
        self.transcript_edit.setFont(QFont("Segoe UI", 10))
        self.transcript_edit.setStyleSheet(
            "QTextEdit { color: #e8e8ff; background: #131325;"
            " border-radius: 6px; padding: 6px;"
            " border: 1px solid #1e1e3a; }"
            "QTextEdit:focus { border: 1px solid #00FFCC; }"
        )
        self.transcript_edit.setPlaceholderText("Captured speech appears here — click to edit or correct...")
        self.transcript_edit.setFixedHeight(75)
        layout.addWidget(self.transcript_edit)

        # ── Manual typing row ─────────────────────────────────────────────────
        type_lbl = QLabel("TYPE A QUESTION")
        type_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        type_lbl.setStyleSheet("color: #888; letter-spacing: 1px;")
        layout.addWidget(type_lbl)

        type_row = QHBoxLayout()
        self.manual_input = QLineEdit()
        self.manual_input.setFont(QFont("Segoe UI", 10))
        self.manual_input.setStyleSheet(
            "QLineEdit { color: #e8e8ff; background: #131325;"
            " border-radius: 6px; padding: 6px 10px;"
            " border: 1px solid #1e1e3a; }"
            "QLineEdit:focus { border: 1px solid #ff8800; }"
        )
        self.manual_input.setPlaceholderText("Type your question here and press Enter or Ask →")
        self.manual_input.returnPressed.connect(self._send_manual)
        type_row.addWidget(self.manual_input, stretch=1)

        ask_btn = QPushButton("Ask →")
        ask_btn.setStyleSheet(_BTN_ORANGE)
        ask_btn.setFixedWidth(70)
        ask_btn.clicked.connect(self._send_manual)
        type_row.addWidget(ask_btn)
        layout.addLayout(type_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #1e1e3a;")
        layout.addWidget(sep2)

        # ── ANSWERS section (scrollable) ──────────────────────────────────────
        ans_row = QHBoxLayout()
        ans_lbl = QLabel("ANSWERS")
        ans_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        ans_lbl.setStyleSheet("color: #00FFCC; letter-spacing: 2px;")
        ans_row.addWidget(ans_lbl, stretch=1)

        self.ans_count_lbl = QLabel("")
        self.ans_count_lbl.setFont(QFont("Segoe UI", 8))
        self.ans_count_lbl.setStyleSheet("color: #555;")
        ans_row.addWidget(self.ans_count_lbl)
        layout.addLayout(ans_row)

        # Scroll area holds all answer cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { background: #1e1e3a; width: 6px; border-radius: 3px; }"
            "QScrollBar::handle:vertical { background: #00FFCC; border-radius: 3px; }"
        )

        self.answers_container = QWidget()
        self.answers_container.setStyleSheet("background: transparent;")
        self.answers_layout = QVBoxLayout(self.answers_container)
        self.answers_layout.setContentsMargins(0, 0, 4, 0)
        self.answers_layout.setSpacing(6)
        self.answers_layout.addStretch()   # pushes cards to top

        self.scroll_area.setWidget(self.answers_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.setCentralWidget(root)

    def _hide_from_capture(self):
        hwnd = int(self.winId())
        result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if result:
            print("Window is INVISIBLE to screen share (Zoom/Meet/Teams).")

    # ── Answer card management ────────────────────────────────────────────────

    def _add_pending_card(self):
        """Create the 'current answer' card that streams tokens into it."""
        self._answer_count += 1
        card = _make_answer_card("⏳ Thinking…", self._answer_count)
        # Grab the text label from the card
        self._pending_card_label = card.layout().itemAt(1).widget()
        # Insert before the stretch item at the end
        insert_pos = self.answers_layout.count() - 1
        self.answers_layout.insertWidget(insert_pos, card)
        self._scroll_to_bottom()
        self.ans_count_lbl.setText(f"{self._answer_count} answer(s)")

    def _finalize_pending_card(self, text: str):
        """Update the pending card with the final answer text."""
        if self._pending_card_label:
            self._pending_card_label.setText(text)
            self._pending_card_label = None
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    # ── Button handlers ───────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._transcriber.flush()
            self.pause_btn.setText("▶ Resume")
            self.pause_btn.setStyleSheet(_BTN_RED)
            self.status_label.setText("⏸ Paused — answering what was heard so far…")
            self.status_label.setStyleSheet("color: #ff4466;")
            QTimer.singleShot(200, lambda: setattr(self._transcriber, "is_paused", True))
        else:
            self._transcriber.is_paused = False
            self.pause_btn.setText("⏸ Pause")
            self.pause_btn.setStyleSheet(_BTN_CYAN)
            self.status_label.setText("🎧 Listening to system audio...")
            self.status_label.setStyleSheet("color: #555;")

    def _reset(self):
        """Clear everything — transcript, all answer cards, AI context."""
        self._transcriber.reset()
        self._ai.reset()
        self._answer_count = 0
        self._pending_card_label = None

        # Remove all widgets from answers_layout except the trailing stretch
        while self.answers_layout.count() > 1:
            item = self.answers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.transcript_edit.clear()
        self.manual_input.clear()
        self.ans_count_lbl.setText("")
        if not self._paused:
            self.status_label.setText("🎧 Listening to system audio...")
            self.status_label.setStyleSheet("color: #555;")

    def _send_manual(self):
        """Send typed question directly to AI (same pipeline as voice input)."""
        text = self.manual_input.text().strip()
        if not text:
            return
        print(f"[Manual] {text}")
        self._transcriber.text_queue.put(text)   # feeds straight into AI worker
        # Show it in the HEARD box too so user can see what was sent
        self.transcript_edit.setPlainText(text)
        self.manual_input.clear()
        self.status_label.setText("📨 Manual question sent...")
        self.status_label.setStyleSheet("color: #00FFCC;")

    def _reask_from_heard(self):
        """Re-send the (possibly edited) HEARD text to the AI."""
        text = self.transcript_edit.toPlainText().strip()
        if not text:
            return
        print(f"[Re-Ask] {text}")
        self._transcriber.text_queue.put(text)
        self.status_label.setText("↩ Re-asking with edited text...")
        self.status_label.setStyleSheet("color: #00FFCC;")

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _refresh(self):
        # ── Transcript (auto-append from voice, don't overwrite if user is editing) ──
        new_transcript = self._ai.get_latest_transcript()
        if new_transcript:
            current = self.transcript_edit.toPlainText()
            combined = (current + " " + new_transcript).strip() if current else new_transcript
            if len(combined) > 300:
                combined = "…" + combined[-300:]
            # Only update if user isn't actively typing in the box
            if not self.transcript_edit.hasFocus():
                self.transcript_edit.setPlainText(combined)

        # ── Streaming partial answer ─────────────────────────────────────────────────
        if self._ai.is_thinking:
            partial = self._ai.partial_answer
            if self._pending_card_label is None:
                self._add_pending_card()   # create card on first thinking frame
            if partial:
                self._pending_card_label.setText(partial)
                self._scroll_to_bottom()
            if not self._paused:
                self.status_label.setText("🤖 Generating answer…")
                self.status_label.setStyleSheet("color: #ffaa00;")
        else:
            # Finalize answer
            answer = self._ai.get_latest_answer()
            if answer:
                if self._pending_card_label is not None:
                    self._finalize_pending_card(answer)
                else:
                    # Answer arrived without a pending card (fast response)
                    self._answer_count += 1
                    card = _make_answer_card(answer, self._answer_count)
                    insert_pos = self.answers_layout.count() - 1
                    self.answers_layout.insertWidget(insert_pos, card)
                    self.ans_count_lbl.setText(f"{self._answer_count} answer(s)")
                    self._scroll_to_bottom()
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
