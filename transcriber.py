import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
CHUNK_SECONDS = 4


class Transcriber:
    def __init__(self, model_size="small.en"):
        # int8 on CPU keeps it fast and light
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._running = False
        self._thread = None

    def start(self, on_text):
        """Start recording. on_text(str) is called for each transcribed chunk."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(on_text,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    def _loop(self, on_text):
        while self._running:
            audio = sd.rec(
                int(CHUNK_SECONDS * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            audio = audio.flatten()

            # skip silent chunks
            if np.abs(audio).max() < 0.01:
                continue

            segments, _ = self.model.transcribe(
                audio,
                language="en",
                vad_filter=True,
                initial_prompt="Programming interview: Python, tuple, dict, list, API, React, SQL.",
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            if text:
                on_text(text)


if __name__ == "__main__":
    import time

    print("Loading model (first run downloads ~150 MB)...")
    t = Transcriber()
    print("Listening for 20 seconds. Speak now!")
    t.start(lambda text: print("->", text))
    time.sleep(20)
    t.stop()
    print("Done.")