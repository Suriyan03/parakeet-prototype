import sys
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel,
)
from transcriber import Transcriber
from llm import stream_answer


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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parakeet Prototype")
        self.resize(700, 600)
        self.transcriber = None
        self.worker = None
        self.bridge = TextBridge()
        self.bridge.text.connect(self.append_transcript)

        self.status = QLabel("Loading speech model...")
        self.transcript_box = QTextEdit(readOnly=True)
        self.transcript_box.setPlaceholderText("Transcription appears here...")
        self.answer_box = QTextEdit(readOnly=True)
        self.answer_box.setPlaceholderText("AI answer appears here...")

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.suggest_btn = QPushButton("Suggest Answer")
        for b in (self.start_btn, self.stop_btn, self.suggest_btn):
            b.setEnabled(False)

        row = QHBoxLayout()
        for b in (self.start_btn, self.stop_btn, self.suggest_btn):
            row.addWidget(b)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addLayout(row)
        layout.addWidget(QLabel("Transcript"))
        layout.addWidget(self.transcript_box)
        layout.addWidget(QLabel("Suggested answer"))
        layout.addWidget(self.answer_box)

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.suggest_btn.clicked.connect(self.on_suggest)

        self.loader = ModelLoader()
        self.loader.loaded.connect(self.on_model_loaded)
        self.loader.start()

    def on_model_loaded(self, transcriber):
        self.transcriber = transcriber
        self.start_btn.setEnabled(True)
        self.suggest_btn.setEnabled(True)
        self.status.setText("Ready. Click Start and speak.")

    def append_transcript(self, text):
        self.transcript_box.append(text)

    def on_start(self):
        self.transcriber.start(self.bridge.text.emit)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status.setText("Listening...")

    def on_stop(self):
        self.status.setText("Stopping...")
        self.transcriber.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status.setText("Stopped.")

    def on_suggest(self):
        transcript = self.transcript_box.toPlainText().strip()
        if not transcript:
            self.status.setText("Nothing transcribed yet.")
            return
        self.answer_box.clear()
        self.suggest_btn.setEnabled(False)
        self.status.setText("Generating answer...")
        self.worker = AnswerWorker(transcript)
        self.worker.token.connect(self.append_token)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_answer_done)
        self.worker.start()

    def append_token(self, tok):
        self.answer_box.insertPlainText(tok)
        self.answer_box.ensureCursorVisible()

    def on_failed(self, msg):
        self.status.setText(f"Error: {msg} (is Ollama running?)")

    def on_answer_done(self):
        self.suggest_btn.setEnabled(True)
        if not self.status.text().startswith("Error"):
            self.status.setText("Done.")

    def closeEvent(self, event):
        if self.transcriber:
            self.transcriber.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())