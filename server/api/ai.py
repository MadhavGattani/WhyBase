# server/api/ai.py
import os
import time

# Get Groq API key (accepts both variable names for flexibility)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("AI_API_KEY")

def call_groq_chat(prompt: str) -> str:
    """
    Uses Groq API for fast inference
    Requires: pip install groq
    """
    try:
        from groq import Groq
        
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create chat completion with Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast and powerful model
            # Alternative models:
            # "llama-3.1-8b-instant" - Faster, smaller
            # "mixtral-8x7b-32768" - Good balance
            # "gemma2-9b-it" - Efficient
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=False
        )
        
        # Extract content from response
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            return content.strip()
        
        return "No response generated"
        
    except Exception as e:
        print(f"[AI] Groq call failed: {e}")
        raise


def call_ai(prompt: str) -> str:
    """
    Top-level AI call used by the app.
    If GROQ_API_KEY is present, try Groq. On failure, fall back to mock.
    """
    if GROQ_API_KEY:
        try:
            return call_groq_chat(prompt)
        except Exception as e:
            # Don't crash the app — fall back to mock and include the error for debugging
            return f"AI (fallback) — error calling Groq:\n\n{e}\n\nMock reply: {prompt[::-1]}"
    
    # Offline/mock fallback
    time.sleep(0.12)
    return f"AI mock response: Received {len(prompt)} characters\n\n{prompt[::-1]}"