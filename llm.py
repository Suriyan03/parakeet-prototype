import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"

SYSTEM_PROMPT = (
    "You are helping someone answer a question during an interview or meeting. "
    "Read the transcript, find the question being asked, and give a clear, "
    "concise answer they can say out loud. Keep it under 120 words."
)


def stream_answer(transcript):
    """Yield the answer token by token from the local Ollama model."""
    payload = {
        "model": MODEL,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    }
    with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            token = data.get("message", {}).get("content", "")
            if token:
                yield token
            if data.get("done"):
                break


if __name__ == "__main__":
    question = "What is the difference between a list and a tuple in Python?"
    print("Q:", question, "\nA: ", end="", flush=True)
    for tok in stream_answer(question):
        print(tok, end="", flush=True)
    print()