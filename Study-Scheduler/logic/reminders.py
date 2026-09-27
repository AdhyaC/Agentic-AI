# ---------- PHASE 4: REMINDERS ----------
# Generates reminders for upcoming deadlines and today's study sessions,
# built directly on top of the schedule/deadline data (Phases 1–3).

from datetime import datetime
from logic.scheduler import days_until, DAYS_ORDER


def get_deadline_reminders(deadlines, today_str, lookahead_days=3):
    """
    Flags deadlines coming up within `lookahead_days`.
    Returns a list of reminder dicts, most urgent first.
    """
    reminders = []

    for d in deadlines:
        distance = days_until(d["date"], today_str)
        if 0 <= distance <= lookahead_days:
            if distance == 0:
                urgency = "Due Today"
            elif distance == 1:
                urgency = "Due Tomorrow"
            else:
                urgency = f"Due in {distance} days"

            reminders.append({
                "course": d["course"],
                "task": d["task"],
                "type": d["type"],
                "date": d["date"],
                "urgency": urgency,
                "days_left": distance,
            })

    return sorted(reminders, key=lambda x: x["days_left"])


def get_today_session_reminders(weekly_table, today_day_name):
    """
    Pulls out today's study sessions from the weekly table
    so they can be shown as "upcoming today" reminders.
    """
    today_blocks = weekly_table.get(today_day_name, [])
    session_reminders = [
        {
            "label": block["label"],
            "start": block["start"],
            "end": block["end"],
        }
        for block in today_blocks
        if block["category"] == "Study"
    ]
    return session_reminders


def get_day_name(date_str):
    """
    Converts a YYYY-MM-DD date string into a day name (Mon, Tue, etc.)
    matching the DAYS_ORDER format used across the app.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return DAYS_ORDER[dt.weekday()]


def build_reminder_summary(deadlines, weekly_table, today_str, lookahead_days=3):
    """
    Combines deadline reminders and today's session reminders
    into a single summary object — ready to serve via /reminders.
    """
    today_day_name = get_day_name(today_str)

    return {
        "date": today_str,
        "day": today_day_name,
        "upcoming_deadlines": get_deadline_reminders(deadlines, today_str, lookahead_days),
        "todays_sessions": get_today_session_reminders(weekly_table, today_day_name),
    }