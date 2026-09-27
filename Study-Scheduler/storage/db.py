# ---------- PHASE 5/6: SIMPLE STORAGE (UPDATED) ----------

_store = {
    "intake": None,
    "weekly_table": None,
    "deadlines": None,
    "preferences": None,
    "feedback_history": [],
}


def save_intake(data):
    _store["intake"] = data
    _store["deadlines"] = data.get("deadlines", [])
    _store["preferences"] = data.get("preferences", {})


def get_intake():
    return _store["intake"]


def save_schedule(weekly_table):
    _store["weekly_table"] = weekly_table


def get_schedule():
    return _store["weekly_table"]


def get_deadlines():
    return _store["deadlines"] or []


def get_preferences():
    return _store["preferences"] or {}


def update_preferences(new_preferences):
    _store["preferences"] = new_preferences
    if _store["intake"]:
        _store["intake"]["preferences"] = new_preferences


def save_feedback_record(record):
    _store["feedback_history"].append(record)


def get_feedback_history():
    return _store["feedback_history"]