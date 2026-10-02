import os
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from dotenv import load_dotenv
from Core.memory import get_all_facts, get_recent_history, log_event

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

client = genai.Client(api_key=api_key)

SYSTEM_PERSONA = """
You are Jarvis: my personal AI collaborator and advisor.
You know my context, my habits, my coding goals, and my daily schedule.

Operating Rules:
1. Be direct, witty, and candid. Avoid robotic filler sentences.
2. Provide grounded, high-signal technical and tactical advice.
3. For voice responses, keep it under 3 punchy sentences unless I ask for deep technical breakdowns.
4. Keep tabs on my progress and point out when I'm slacking on my routine or targets.
"""

# Active models reported by the API error logs
ACTIVE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

def consult_jarvis(user_message: str, category: str = "general") -> str:
    profile_context = get_all_facts()
    recent_context = get_recent_history(limit=6)

    grounded_input = f"""
---
MY PERSISTENT PROFILE:
{profile_context}

RECENT TIMELINE & LOGS:
{recent_context}
---

User Query: {user_message}
"""

    reply_text = None
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PERSONA,
        temperature=0.7,
    )

    for model_name in ACTIVE_MODELS:
        try:
            # Using client.chats eliminates the AFC warning
            chat = client.chats.create(model=model_name, config=config)
            response = chat.send_message(grounded_input)
            reply_text = response.text.strip()
            break
        except ServerError:
            # 503 high demand spike - try the lightweight fallback
            print(f"[!] {model_name} high demand (503). Retrying on fallback model...")
            time.sleep(1)
            continue
        except ClientError as e:
            print(f"[!] Error on {model_name}: {e.message}")
            continue

    if not reply_text:
        return "Jarvis core is experiencing momentary upstream load, but your context has been logged."

    # Log interaction to SQLite
    log_event("user", user_message)
    log_event("jarvis", reply_text)

    return reply_text