"""memory.py - remembers user preferences in a small JSON file."""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preferences.json")


def load_preferences():
    """Return saved preferences as a dict ({} if none yet)."""
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_preferences(updates):
    """Merge `updates` (dict) into saved preferences, write to disk, return the result."""
    prefs = load_preferences()
    prefs.update(updates)
    with open(PATH, "w") as f:
        json.dump(prefs, f, indent=2)
    return prefs