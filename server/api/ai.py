import os
AI_KEY = os.getenv("AI_API_KEY")

def call_ai(prompt: str) -> str:
    # placeholder — later replace with real provider call
    return f"AI mock response: Received {len(prompt)} characters\n\n{prompt[::-1]}"
