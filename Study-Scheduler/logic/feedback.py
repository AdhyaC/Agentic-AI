# ---------- PHASE 6: FEEDBACK LOOP / ADAPTABILITY ----------
# Takes weekly check-in input (what worked / what didn't) and
# adjusts preferences or deadlines handling for the next schedule.
# Rule-based adjustment only — no ML, per project constraints.

def apply_feedback(preferences, feedback):
    """
    Adjusts scheduling preferences based on simple feedback signals.
    feedback expected shape:
    {
        "missed_sessions": int,
        "felt_too_packed": bool,
        "felt_too_light": bool,
        "preferred_session_length_change": int  # e.g. -10, +10, or 0
    }
    """
    updated = preferences.copy()

    # Rule 1: too many missed sessions -> shorten session length slightly
    if feedback.get("missed_sessions", 0) >= 3:
        updated["session_length_minutes"] = max(
            20, updated["session_length_minutes"] - 10
        )

    # Rule 2: felt too packed -> increase break length
    if feedback.get("felt_too_packed"):
        updated["break_length_minutes"] = min(
            20, updated["break_length_minutes"] + 5
        )

    # Rule 3: felt too light -> decrease break length slightly
    if feedback.get("felt_too_light"):
        updated["break_length_minutes"] = max(
            5, updated["break_length_minutes"] - 5
        )

    # Rule 4: direct session length adjustment request
    change = feedback.get("preferred_session_length_change", 0)
    if change:
        updated["session_length_minutes"] = max(
            20, updated["session_length_minutes"] + change
        )

    return updated


def build_feedback_record(week_of, feedback, updated_preferences):
    """
    Packages a feedback submission into a storable record,
    including what changed as a result — useful for showing
    the student *why* next week's plan is different.
    """
    return {
        "week_of": week_of,
        "feedback": feedback,
        "updated_preferences": updated_preferences,
    }