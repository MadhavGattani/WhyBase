# server/api/ai.py
import os
import time

# Try to get either variable name (we accept both)
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")

def call_openai_chat(prompt: str) -> str:
    """
    Uses the new openai-python >=1.0 client.
    Requires: pip install openai (>=1.0)
    """
    try:
        # Import here so the file can still be imported when 'openai' isn't installed
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)

        # Create chat completion (this is the new interface)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",  # adjust to gpt-4 or other model if you have access
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )

        # Response shape: resp.choices[0].message.content
        # Defensive access:
        content = ""
        if getattr(resp, "choices", None):
            first = resp.choices[0]
            # Support structure where message may be nested
            if getattr(first, "message", None) and getattr(first.message, "content", None):
                content = first.message.content
            elif getattr(first, "delta", None) and getattr(first.delta, "content", None):
                content = first.delta.content
            else:
                # fallback to converting whole choice to string
                content = str(first)
        else:
            content = str(resp)

        return content.strip()
    except Exception as e:
        # Surface a short log and re-raise so caller can fall back if desired
        print(f"[AI] OpenAI call failed: {e}")
        raise

def call_ai(prompt: str) -> str:
    """
    Top-level AI call used by the app.
    If OPENAI_KEY is present, try OpenAI (new client). On failure, fall back to mock.
    """
    if OPENAI_KEY:
        try:
            return call_openai_chat(prompt)
        except Exception as e:
            # don't crash the app — fall back to mock and include the error for debugging
            return f"AI (fallback) — error calling OpenAI:\n\n{e}\n\nMock reply: {prompt[::-1]}"
    # Offline/mock fallback
    time.sleep(0.12)
    return f"AI mock response: Received {len(prompt)} characters\n\n{prompt[::-1]}"