# ---------- PHASE 3: WEEKLY PLANNER OUTPUT ----------
# Takes the raw schedule from scheduler.py and formats it into
# a clean weekly table structure (days x time blocks), merging in
# hobbies and fixed commitments so the full week is visible.

from logic.scheduler import DAYS_ORDER, time_to_minutes, minutes_to_time


def build_weekly_table(study_schedule, hobbies, fixed_commitments):
    """
    Combines study sessions, hobbies, and fixed commitments into
    a single weekly table: { day: [ {start, end, label, category} ] }
    sorted chronologically per day.
    """
    table = {day: [] for day in DAYS_ORDER}

    # Add study sessions
    for day, sessions in study_schedule.items():
        for s in sessions:
            table[day].append({
                "start": s["start"],
                "end": s["end"],
                "label": f'{s["course"]} — {s["task"]}',
                "category": "Study",
            })

    # Add hobbies
    for h in hobbies:
        for day in h["days"]:
            table[day].append({
                "start": h["start"],
                "end": h["end"],
                "label": h["label"],
                "category": "Hobby",
            })

    # Add fixed commitments (class, job, sleep, club)
    for c in fixed_commitments:
        for day in c["days"]:
            table[day].append({
                "start": c["start"],
                "end": c["end"],
                "label": c["label"],
                "category": "Fixed",
            })

    # Sort each day chronologically
    for day in DAYS_ORDER:
        table[day].sort(key=lambda x: time_to_minutes(x["start"]))

    return table


def print_table(table):
    """
    Simple console/text rendering of the weekly table for
    quick verification before the frontend exists.
    """
    for day in DAYS_ORDER:
        print(f"\n=== {day} ===")
        if not table[day]:
            print("  (nothing scheduled)")
            continue
        for block in table[day]:
            print(f'  {block["start"]}–{block["end"]}  [{block["category"]}]  {block["label"]}')


def table_to_json(table):
    """
    Returns the table as a plain dict, ready to be serialized
    as JSON for the /generate-schedule API response.
    """
    return table