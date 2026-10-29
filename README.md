# 🦜 Parakeet Prototype

A small desktop app, inspired by Parakeet AI, that listens to your microphone, transcribes speech, and suggests an answer to the question it heard. **Speech-to-text and the LLM both run locally. No cloud APIs, no API keys, and no audio leaves your computer.**

![App screenshot](screenshot.png)

## ✨ Features

- Start / Stop buttons for microphone capture
- Live transcription with **faster-whisper** (`small.en`)
- **Suggest Answer** button that streams the reply token by token using **Ollama** (`llama3.2:3b`)
- Dark-themed desktop UI built with **PySide6**

## 🧰 Tech Stack

| Component       | Technology                  |
| --------------- | --------------------------- |
| Desktop UI      | Python + PySide6            |
| Microphone      | sounddevice                 |
| Speech-to-text  | faster-whisper (local, CPU) |
| LLM             | Ollama + Llama 3.2 3B       |
| Streaming       | Ollama streaming HTTP API   |

## ✅ Prerequisites

- Windows 10/11 or macOS
- Python **3.10 or newer** ([download](https://www.python.org/downloads/))
- A working microphone
- About 3 GB of free disk space (models) and 8 GB RAM recommended
- [Git](https://git-scm.com/downloads) (to clone the repo)

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/parakeet-prototype.git
cd parakeet-prototype
```

### 2. Install Ollama and download the model

1. Download and install Ollama from [ollama.com/download](https://ollama.com/download).
2. Open a **new** terminal and verify the install:

```bash
ollama --version
```

3. Download the model (about 2 GB):

```bash
ollama pull llama3.2:3b
```

4. (Optional) Test it:

```bash
ollama run llama3.2:3b
```

Type `/bye` to exit. Ollama keeps running in the background (tray/menu bar icon), which is all the app needs.

### 3. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
```

> If PowerShell blocks the activation script, run this once and try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal line.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Run the App

1. Make sure Ollama is running.
2. Start the app:

```bash
python app.py
```

3. Wait for the status pill to show **Ready** (the first run downloads the Whisper model, about 480 MB, so it takes a minute).
4. Click **Start** and speak a question, for example *"What is the difference between a tuple and a dict in Python?"*
5. Click **Stop**.
6. Click **Suggest Answer** and watch the answer stream in.

## 📁 Project Structure

```
parakeet-prototype/
├── app.py              # PySide6 window and wiring
├── transcriber.py      # Mic capture + faster-whisper transcription
├── llm.py              # Streaming calls to the local Ollama API
├── requirements.txt    # Python dependencies
└── README.md
```

## ⚙️ How It Works

1. **Capture:** `sounddevice` records the microphone in 4-second chunks on a background thread.
2. **Transcribe:** each chunk goes through faster-whisper (CPU, int8), and the text is appended to the transcript box.
3. **Answer:** on **Suggest Answer**, the transcript is sent to Ollama at `http://localhost:11434/api/chat` with `stream: true`.
4. **Stream:** a worker thread emits each token through a Qt signal, so the answer appears progressively without freezing the UI.

## 🔧 Configuration

| What                     | Where                         | Default       |
| ------------------------ | ----------------------------- | ------------- |
| Whisper model size       | `transcriber.py` (`__init__`) | `small.en`    |
| Audio chunk length       | `transcriber.py`              | `4` seconds   |
| Ollama model             | `llm.py` (`MODEL`)            | `llama3.2:3b` |
| Answer style / length    | `llm.py` (`SYSTEM_PROMPT`)    | under 120 words |

Faster but less accurate: use `base.en`. More accurate but slower: use `medium.en`. For better answers, try `ollama pull llama3.1:8b` and set `MODEL` to it.

## 🩹 Troubleshooting

| Problem | Fix |
| ------- | --- |
| `ollama` is not recognized | Close and reopen the terminal (or VS Code) after installing Ollama. |
| "Error: is Ollama running?" in the app | Start the Ollama app from the Start menu / Applications, then click Suggest Answer again. |
| Model not found | Run `ollama list` and confirm `llama3.2:3b` is listed. If not, run `ollama pull llama3.2:3b`. |
| No transcription appears | Allow microphone access: Windows → Settings → Privacy & security → Microphone (enable for desktop apps). macOS → System Settings → Privacy & Security → Microphone (enable for your terminal/VS Code). |
| Wrong microphone is used | List devices with `python -c "import sounddevice as sd; print(sd.query_devices())"` and set the default input device in your OS sound settings. |
| Technical words are misheard | Use a larger Whisper model, or edit the `initial_prompt` in `transcriber.py` with your own vocabulary. |
| First launch is slow | The Whisper model is downloading. Later runs start in seconds. |

## 📝 Notes and Limitations

- This is a prototype: audio is processed in fixed 4-second chunks, so a word may occasionally be cut between chunks.
- A 3B model can make factual mistakes. Always double-check important answers.
- Everything runs on CPU by default; a GPU is not required.

## 📄 License

Released for assignment/demo purposes. Feel free to learn from it and adapt it.
