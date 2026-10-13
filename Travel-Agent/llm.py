"""llm.py - the single place the agent talks to the LLM (Groq)."""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # reads the .env file in this folder

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")

MODEL = "openai/gpt-oss-120b"
_client = Groq(api_key=GROQ_API_KEY)


def call_llm(prompt, system="You are a helpful travel assistant.", json_mode=False):
    """Send a prompt to Groq and return the reply as a string.

    Input:  prompt (str), system (str), json_mode (bool, forces a JSON reply)
    Output: reply text (str, empty string if the model returns nothing)
    """
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        **kwargs,
    )
    return response.choices[0].message.content or ""