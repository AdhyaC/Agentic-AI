# ---------- PHASE 2: SCHEDULING LOGIC ----------

from datetime import datetime

DAYS_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def days_until(deadline_date_str, today_str):
    """Return number of days between today and a deadline."""
    deadline = datetime.strptime(deadline_date_str, "%Y-%m-%d")
    today = datetime.strptime(today_str, "%Y-%m-%d")
    return (deadline - today).days


def prioritize_deadlines(deadlines, today_str):
    """
    Rule: closer deadlines get higher priority.
    Exams/Projects/Papers are weighted higher than quizzes/homework
    at the same distance, since they typically need more prep time.
    """
    type_weight = {
        "Exam": 3,
        "Project": 2,
        "Paper": 2,
        "Lab": 1.5,
        "Quiz": 1,
        "Homework": 1,
    }

    scored = []
    for d in deadlines:
        distance = days_until(d["date"], today_str)
        if distance < 0:
            continue  # skip past deadlines
        weight = type_weight.get(d["type"], 1)
        # Lower score = higher priority (closer + heavier type)
        score = distance / weight
        scored.append({**d, "priority_score": score, "days_left": distance})

    return sorted(scored, key=lambda x: x["priority_score"])


def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def minutes_to_time(mins):
    h = (mins // 60) % 24
    m = mins % 60
    return f"{h:02d}:{m:02d}"


def get_free_slots(available_study_hours, fixed_commitments, hobbies):
    """
    Build a per-day list of free time windows by subtracting
    fixed commitments and hobbies from available study hours.
    """
    free_slots = {day: [] for day in DAYS_ORDER}

    # Start with available study windows per day
    for window in available_study_hours:
        for day in window["days"]:
            free_slots[day].append(
                (time_to_minutes(window["start"]), time_to_minutes(window["end"]))
            )

    # Collect blocked ranges (commitments + hobbies) per day
    blocked = {day: [] for day in DAYS_ORDER}
    for item in fixed_commitments + hobbies:
        for day in item["days"]:
            blocked[day].append(
                (time_to_minutes(item["start"]), time_to_minutes(item["end"]))
            )

    # Subtract blocked ranges from free windows
    result = {day: [] for day in DAYS_ORDER}
    for day in DAYS_ORDER:
        for start, end in free_slots[day]:
            segments = [(start, end)]
            for b_start, b_end in blocked[day]:
                new_segments = []
                for s, e in segments:
                    if b_end <= s or b_start >= e:
                        new_segments.append((s, e))  # no overlap
                    else:
                        if b_start > s:
                            new_segments.append((s, b_start))
                        if b_end < e:
                            new_segments.append((b_end, e))
                segments = new_segments
            result[day].extend(segments)

    return result


def allocate_sessions(prioritized_deadlines, free_slots, preferences):
    """
    Place study sessions into free slots, spreading across days,
    respecting session/break length preferences.
    """
    session_len = preferences["session_length_minutes"]
    break_len = preferences["break_length_minutes"]
    block_len = session_len + break_len

    schedule = {day: [] for day in DAYS_ORDER}
    day_cursor = {day: 0 for day in DAYS_ORDER}  # tracks slot index in use

    day_rotation = DAYS_ORDER.copy()
    rotation_index = 0

    for deadline in prioritized_deadlines:
        placed = False
        attempts = 0

        while not placed and attempts < len(day_rotation):
            day = day_rotation[rotation_index % len(day_rotation)]
            rotation_index += 1
            attempts += 1

            slots = free_slots.get(day, [])
            for i, (start, end) in enumerate(slots):
                if end - start >= session_len:
                    schedule[day].append({
                        "course": deadline["course"],
                        "task": deadline["task"],
                        "start": minutes_to_time(start),
                        "end": minutes_to_time(start + session_len),
                    })
                    new_start = start + block_len
                    if new_start < end:
                        slots[i] = (new_start, end)
                    else:
                        slots.pop(i)
                    placed = True
                    break

    return schedule