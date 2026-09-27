from datetime import date

from logic.planner_output import build_weekly_table
from logic.scheduler import allocate_sessions, get_free_slots, minutes_to_time, prioritize_deadlines, time_to_minutes


def create_weekly_schedule(intake, today_str=None):
    if today_str is None:
        today_str = date.today().isoformat()

    prioritized = prioritize_deadlines(intake["deadlines"], today_str)
    free_slots = get_free_slots(
        intake["available_study_hours"],
        intake["fixed_commitments"],
        intake["hobbies"],
    )
    study_schedule = allocate_sessions(prioritized, free_slots, intake["preferences"])
    weekly_table = build_weekly_table(
        study_schedule, intake["hobbies"], intake["fixed_commitments"]
    )

    for override in intake.get("schedule_overrides", []):
        excluded_day = override.get("excluded_day")
        if excluded_day in weekly_table:
            weekly_table[excluded_day] = [
                block
                for block in weekly_table[excluded_day]
                if block["category"] != "Study" or block["label"] != override["label"]
            ]
            continue

        if "day" not in override or "start" not in override:
            continue

        matches = [
            (day, block)
            for day, blocks in weekly_table.items()
            for block in blocks
            if block["category"] == "Study" and block["label"] == override["label"]
        ]
        new_day = override["day"]
        if len(matches) != 1 or new_day not in weekly_table:
            continue

        old_day, block = matches[0]
        new_start = time_to_minutes(override["start"])
        duration = time_to_minutes(block["end"]) - time_to_minutes(block["start"])
        new_end = new_start + duration
        available = any(
            new_day in window["days"]
            and time_to_minutes(window["start"]) <= new_start
            and new_end <= time_to_minutes(window["end"])
            for window in intake["available_study_hours"]
        )
        conflicts = any(
            other is not block
            and new_start < time_to_minutes(other["end"])
            and time_to_minutes(other["start"]) < new_end
            for other in weekly_table[new_day]
        )
        if not available or conflicts:
            continue

        weekly_table[old_day].remove(block)
        block["start"] = minutes_to_time(new_start)
        block["end"] = minutes_to_time(new_end)
        weekly_table[new_day].append(block)
        weekly_table[new_day].sort(key=lambda item: time_to_minutes(item["start"]))

    return weekly_table