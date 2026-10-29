# Parakeet Prototype

A small desktop app that transcribes microphone audio and suggests an answer, with everything running locally (no cloud APIs).

## Features
- Start / Stop buttons for microphone capture
- Live transcription (faster-whisper, `small.en`)
- "Suggest Answer" button that streams an answer token by token (Ollama, `llama3.2:3b`)

## Tech stack
Python, PySide6, sounddevice, faster-whisper, Ollama

## Setup
1. Install Python 3.10+
2. Install Ollama from https://ollama.com, then run: `ollama pull llama3.2:3b`
3. Create and activate a virtual environment:
   - `python -m venv venv`
   - Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`

## Run
1. Make sure Ollama is running (the llama icon in the system tray).
2. `python app.py`
3. Wait for "Ready", click **Start**, speak a question, click **Stop**, then **Suggest Answer**.

Note: the first run downloads the Whisper model (~480 MB).

## Files
- `app.py`: PySide6 window and wiring
- `transcriber.py`: mic capture + speech-to-text
- `llm.py`: streaming calls to the local Ollama API