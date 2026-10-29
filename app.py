import sys
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel,
)
from transcriber import Transcriber
from llm import stream_answer

STYLE = """
QWidget { background: #0f1117; color: #e6e8ee; font-family: 'Segoe UI'; font-size: 14px; }
QLabel { background: transparent; }
QLabel#title { font-size: 22px; font-weight: 700; }
QLabel#subtitle { color: #8b90a0; font-size: 12px; }
QLabel#section { color: #8b90a0; font-size: 11px; font-weight: 700; }

QLabel#status { padding: 6px 14px; border-radius: 13px; background: #1a1d27; color: #8b90a0; }
QLabel#status[state="ready"]   { background: #12301f; color: #4ade80; }
QLabel#status[state="listen"]  { background: #3a1517; color: #f87171; }
QLabel#status[state="busy"]    { background: #2a2410; color: #facc15; }
QLabel#status[state="error"]   { background: #3a1517; color: #f87171; }

QTextEdit { background: #171a23; border: 1px solid #262a37; border-radius: 12px;
            padding: 12px; font-size: 15px; selection-background-color: #4f46e5; }
QTextEdit:focus { border: 1px solid #4f46e5; }

QPushButton { border: none; border-radius: 10px; padding: 11px 20px;
              font-weight: 600; background: #262a37; color: #e6e8ee; }
QPushButton:hover { background: #30354a; }
QPushButton:disabled { background: #171a23; color: #4b5163; }
QPushButton#start   { background: #22c55e; color: #052e14; }
QPushButton#start:hover   { background: #4ade80; }
QPushButton#stop    { background: #ef4444; color: #ffffff; }
QPushButton#stop:hover    { background: #f87171; }
QPushButton#suggest { background: #4f46e5; color: #ffffff; }
QPushButton#suggest:hover { background: #6366f1; }
QPushButton#start:disabled, QPushButton#stop:disabled, QPushButton#suggest:disabled {
    background: #171a23; color: #4b5163; }
"""


class ModelLoader(QThread):
    loaded = Signal(object)

    def run(self):
        self.loaded.emit(Transcriber())


class AnswerWorker(QThread):
    token = Signal(str)
    failed = Signal(str)

    def __init__(self, transcript):
        super().__init__()
        self.transcript = transcript

    def run(self):
        try:
            for t in stream_answer(self.transcript):
                self.token.emit(t)
        except Exception as e:
            self.failed.emit(str(e))


class TextBridge(QObject):
    text = Signal(str)


def section(text):
    lbl = QLabel(text.upper())
    lbl.setObjectName("section")
    return lbl


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parakeet Prototype")
        self.resize(760, 680)
        self.transcriber = None
        self.worker = None
        self.bridge = TextBridge()
        self.bridge.text.connect(self.append_transcript)

        # Header
        title = QLabel("Parakeet Prototype")
        title.setObjectName("title")
        subtitle = QLabel("Local speech-to-text + local LLM. Nothing leaves your computer.")
        subtitle.setObjectName("subtitle")
        self.status = QLabel()
        self.status.setObjectName("status")
        self.set_status("Loading speech model...", "busy")

        head_text = QVBoxLayout()
        head_text.setSpacing(2)
        head_text.addWidget(title)
        head_text.addWidget(subtitle)
        header = QHBoxLayout()
        header.addLayout(head_text)
        header.addStretch()
        header.addWidget(self.status)

        # Text areas
        self.transcript_box = QTextEdit(readOnly=True)
        self.transcript_box.setPlaceholderText("Click Start and speak. Your words appear here...")
        self.answer_box = QTextEdit(readOnly=True)
        self.answer_box.setPlaceholderText("Click Suggest Answer to get a streamed reply...")

        # Buttons
        self.start_btn = QPushButton("●  Start")
        self.start_btn.setObjectName("start")
        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setObjectName("stop")
        self.suggest_btn = QPushButton("✦  Suggest Answer")
        self.suggest_btn.setObjectName("suggest")
        for b in (self.start_btn, self.stop_btn, self.suggest_btn):
            b.setEnabled(False)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        row.addStretch()
        row.addWidget(self.suggest_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(10)
        layout.addLayout(header)
        layout.addSpacing(6)
        layout.addLayout(row)
        layout.addSpacing(4)
        layout.addWidget(section("Transcript"))
        layout.addWidget(self.transcript_box, 1)
        layout.addWidget(section("Suggested answer"))
        layout.addWidget(self.answer_box, 2)

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.suggest_btn.clicked.connect(self.on_suggest)

        self.loader = ModelLoader()
        self.loader.loaded.connect(self.on_model_loaded)
        self.loader.start()

    def set_status(self, text, state):
        self.status.setText(text)
        self.status.setProperty("state", state)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def on_model_loaded(self, transcriber):
        self.transcriber = transcriber
        self.start_btn.setEnabled(True)
        self.suggest_btn.setEnabled(True)
        self.set_status("Ready", "ready")

    def append_transcript(self, text):
        self.transcript_box.append(text)

    def on_start(self):
        self.transcriber.start(self.bridge.text.emit)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.set_status("● Listening", "listen")

    def on_stop(self):
        self.set_status("Stopping...", "busy")
        self.transcriber.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.set_status("Stopped", "ready")

    def on_suggest(self):
        transcript = self.transcript_box.toPlainText().strip()
        if not transcript:
            self.set_status("Nothing transcribed yet", "error")
            return
        self.answer_box.clear()
        self.suggest_btn.setEnabled(False)
        self.set_status("Generating answer...", "busy")
        self.worker = AnswerWorker(transcript)
        self.worker.token.connect(self.append_token)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_answer_done)
        self.worker.start()

    def append_token(self, tok):
        self.answer_box.insertPlainText(tok)
        self.answer_box.ensureCursorVisible()

    def on_failed(self, msg):
        self.set_status("Error: is Ollama running?", "error")

    def on_answer_done(self):
        self.suggest_btn.setEnabled(True)
        if self.status.property("state") != "error":
            self.set_status("Done", "ready")

    def closeEvent(self, event):
        if self.transcriber:
            self.transcriber.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())