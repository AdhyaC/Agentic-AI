import re
from difflib import SequenceMatcher
from datetime import datetime

from logic.planning import create_weekly_schedule
from logic.scheduler import minutes_to_time, time_to_minutes
from storage.db import (
    get_deadlines,
    get_intake,
    get_preferences,
    get_schedule,
    save_intake,
    save_schedule,
    update_preferences,
)

SESSION_PATTERNS = (
    re.compile(r"\b(?:sessions?|focus(?:\s+blocks?)?)\b[^\d]{0,22}(\d{2,3})\s*(?:minutes?|mins?|m)\b", re.IGNORECASE),
    re.compile(r"\b(\d{2,3})\s*[- ]?(?:minutes?|mins?)\s+(?:focus\s+)?sessions?\b", re.IGNORECASE),
)
BREAK_PATTERNS = (
    re.compile(r"\b(?:breaks?|break length)\b[^\d]{0,22}(\d{1,2})\s*(?:minutes?|mins?|m)\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*[- ]?(?:minutes?|mins?)\s+breaks?\b", re.IGNORECASE),
)
DEADLINE_PATTERN = re.compile(
    r"\b(?:add|create|include)\s+(?:a\s+)?deadline\s+for\s+([^:]+):\s*(.+?),?\s+due\s+(\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
MOVE_PATTERN = re.compile(
    r"\b(?:move|reschedule)\s+(.+?)\s+(?:to|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
    re.IGNORECASE,
)
REMOVE_PATTERN = re.compile(
    r"\b(?:remove|delete)\s+(.+?)\s+(?:from\s+)?(?:on\s+)?(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b",
    re.IGNORECASE,
)
CHANGE_COMMITMENT_PATTERN = re.compile(
    r"\b(?:change|rename|replace)\s+(.+?)\s+on\s+(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\s+to\s+(.+?)\s*[.!?]*$",
    re.IGNORECASE,
)
DURATION_ADJUST_PATTERN = re.compile(
    r"\b(extend|lengthen|increase|shorten|reduce|decrease)\s+(.+?)(?:\s+on\s+(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?))?\s+by\s+(\d{1,3})\s*(?:minutes?|mins?|m)\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", re.IGNORECASE)
DAY_PATTERN = re.compile(r"\b(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b", re.IGNORECASE)
DAYS = {
    "mon": "Mon", "monday": "Mon",
    "tue": "Tue", "tuesday": "Tue",
    "wed": "Wed", "wednesday": "Wed",
    "thu": "Thu", "thursday": "Thu",
    "fri": "Fri", "friday": "Fri",
    "sat": "Sat", "saturday": "Sat",
    "sun": "Sun", "sunday": "Sun",
}


def generate_reply(message, weekly_table=None):
    """Answer read-only questions about the current plan."""
    message_lower = message.lower()

    if "today" in message_lower:
        return "Your weekly timetable is shown above. Tell me what you want changed and I can update it."

    if "deadline" in message_lower or "due" in message_lower:
        deadlines = get_deadlines()
        today = datetime.today().date().isoformat()
        upcoming = [deadline for deadline in deadlines if deadline["date"] >= today]
        if upcoming:
            closest = min(upcoming, key=lambda deadline: deadline["date"])
            return f"Your closest deadline is {closest['task']} for {closest['course']}, due {closest['date']}."
        return "There are no upcoming deadlines in your planner."

    if "session" in message_lower and ("long" in message_lower or "length" in message_lower):
        return f"Your focus sessions are currently {get_preferences().get('session_length_minutes', 50)} minutes long."

    return "I can change session or break lengths, add a dated deadline, move a study block, or rebuild your timetable."


def _find_minutes(patterns, message):
    for pattern in patterns:
        match = pattern.search(message)
        if match:
            return int(match.group(1))
    return None


def _matches_words(words, label):
    label_words = re.findall(r"[a-z0-9]+", label.lower())
    return all(
        any(
            word == label_word
            or word in label_word
            or (len(word) >= 5 and len(label_word) >= 5 and SequenceMatcher(None, word, label_word).ratio() >= 0.84)
            for label_word in label_words
        )
        for word in words
    )


def _rebuild(intake, reply, action):
    save_intake(intake)
    weekly_table = create_weekly_schedule(intake)
    save_schedule(weekly_table)
    return {
        "status": "ok",
        "reply": reply,
        "action": action,
        "intake": intake,
        "weekly_table": weekly_table,
    }


def _change_preferences(message, intake):
    preferences = dict(intake["preferences"])
    requested = {}
    session_length = _find_minutes(SESSION_PATTERNS, message)
    break_length = _find_minutes(BREAK_PATTERNS, message)

    if session_length is not None:
        if not 15 <= session_length <= 180:
            return {"status": "ok", "reply": "Focus sessions need to be between 15 and 180 minutes. What length should I use?"}
        requested["session_length_minutes"] = session_length

    if break_length is not None:
        if not 0 <= break_length <= 60:
            return {"status": "ok", "reply": "Breaks need to be between 0 and 60 minutes. What length should I use?"}
        requested["break_length_minutes"] = break_length

    lower = message.lower()
    if not requested and any(word in lower for word in ("overwhelmed", "overwhelm", "too packed", "lighter")):
        requested["session_length_minutes"] = min(preferences["session_length_minutes"], 40)
        requested["break_length_minutes"] = max(preferences["break_length_minutes"], 15)

    if not requested:
        return None

    preferences.update(requested)
    updated_intake = {**intake, "preferences": preferences}
    changes = []
    if "session_length_minutes" in requested:
        changes.append(f"{requested['session_length_minutes']}-minute focus sessions")
    if "break_length_minutes" in requested:
        changes.append(f"{requested['break_length_minutes']}-minute breaks")
    return _rebuild(
        updated_intake,
        f"Done. I updated your plan with {' and '.join(changes)}.",
        "preferences_updated",
    )


def _add_deadline(message, intake):
    match = DEADLINE_PATTERN.search(message)
    if not match:
        return None

    course_name, task, due_date = (part.strip() for part in match.groups())
    if course_name.lower().startswith("the "):
        course_name = course_name[4:]
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return {"status": "ok", "reply": "I couldn't read that date. Send it as YYYY-MM-DD and I'll add it."}

    task_lower = task.lower()
    if any(word in task_lower for word in ("exam", "midterm", "final")):
        task_type = "Exam"
    elif "project" in task_lower or "presentation" in task_lower:
        task_type = "Project"
    elif "paper" in task_lower or "essay" in task_lower:
        task_type = "Paper"
    elif "lab" in task_lower:
        task_type = "Lab"
    elif "quiz" in task_lower:
        task_type = "Quiz"
    else:
        task_type = "Homework"

    updated_intake = {
        **intake,
        "courses": list(intake["courses"]),
        "deadlines": [*intake["deadlines"], {
            "course": course_name,
            "task": task,
            "type": task_type,
            "date": due_date,
        }],
    }
    if not any(course["name"].lower() == course_name.lower() for course in updated_intake["courses"]):
        updated_intake["courses"].append({"name": course_name, "credits": 3, "difficulty": "Medium"})

    return _rebuild(
        updated_intake,
        f"Added {task} for {course_name}, due {due_date}, and rebuilt your timetable.",
        "deadline_added",
    )


def _parse_time(value):
    match = TIME_PATTERN.match(value.strip())
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = (match.group(3) or "").lower()
    if minute > 59 or hour > (12 if period else 23) or hour == 0 and period:
        return None
    if period == "pm" and hour < 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0
    return hour * 60 + minute


def _move_study_block(message):
    match = MOVE_PATTERN.search(message)
    if not match:
        return None

    table = get_schedule()
    intake = get_intake()
    if not table or not intake:
        return {"status": "ok", "reply": "I don't have a timetable to move yet. Ask me to rebuild your week first."}

    new_start = _parse_time(match.group(2))
    if new_start is None:
        return {"status": "ok", "reply": "I couldn't read that time. Try a time like 11am or 14:30."}

    target_day_match = DAY_PATTERN.search(message)
    target_day = DAYS[target_day_match.group(1).lower()] if target_day_match else None
    target = DAY_PATTERN.sub(" ", match.group(1).lower())
    target = re.sub(r"\b(on|to|at|my|the|this|that|it|study|session|block)\b", " ", target)
    target_words = re.findall(r"[a-z0-9]+", target)

    study_blocks = [
        (day, block)
        for day, blocks in table.items()
        for block in blocks
        if block["category"] == "Study" and (target_day is None or day == target_day)
    ]
    if target_words:
        study_blocks = [
            (day, block)
            for day, block in study_blocks
            if _matches_words(target_words, block["label"])
        ]

    if len(study_blocks) != 1:
        if not study_blocks:
            return {"status": "ok", "reply": "I couldn't find a matching study block. Include its course or task name."}
        choices = "; ".join(f"{day}: {block['label']}" for day, block in study_blocks[:3])
        return {"status": "ok", "reply": f"Which study block should I move? I found {choices}."}

    old_day, block = study_blocks[0]
    new_day = target_day or old_day
    duration = time_to_minutes(block["end"]) - time_to_minutes(block["start"])
    new_end = new_start + duration
    if new_end > 24 * 60:
        return {"status": "ok", "reply": "That time would push the study block past midnight. Choose an earlier time."}

    available = any(
        new_day in window["days"]
        and time_to_minutes(window["start"]) <= new_start
        and new_end <= time_to_minutes(window["end"])
        for window in intake["available_study_hours"]
    )
    if not available:
        return {"status": "ok", "reply": f"{new_day} at {minutes_to_time(new_start)} is outside your available study hours. Tell me another time or day."}

    for other in table[new_day]:
        if other is block:
            continue
        other_start = time_to_minutes(other["start"])
        other_end = time_to_minutes(other["end"])
        if new_start < other_end and other_start < new_end:
            return {"status": "ok", "reply": f"That overlaps with {other['label']} at {other['start']}–{other['end']}. Pick another time and I'll move it."}

    overrides = [
        override
        for override in intake.get("schedule_overrides", [])
        if override["label"] != block["label"]
    ]
    overrides.append({
        "label": block["label"],
        "day": new_day,
        "start": minutes_to_time(new_start),
    })
    updated_intake = {**intake, "schedule_overrides": overrides}
    day_name = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}[new_day]
    return _rebuild(
        updated_intake,
        f"Done. Moved {block['label']} to {day_name} at {minutes_to_time(new_start)}; I checked it against your other blocks.",
        "study_block_moved",
    )


def _remove_study_blocks(message):
    match = REMOVE_PATTERN.search(message)
    if not match:
        return None

    intake = get_intake()
    table = get_schedule()
    if not intake or not table:
        return {"status": "ok", "reply": "I don't have a timetable to update yet. Ask me to rebuild your week first."}

    day = DAYS[match.group(2).lower()]
    course_query = DAY_PATTERN.sub(" ", match.group(1).lower())
    course_query = re.sub(r"\b(course|class|study|block|session|the|my)\b", " ", course_query)
    course_words = re.findall(r"[a-z0-9]+", course_query)
    if not course_words:
        return {"status": "ok", "reply": "Which course should I remove from that day?"}

    study_matches = [
        block
        for block in table[day]
        if block["category"] == "Study"
        and _matches_words(course_words, block["label"])
    ]
    commitment_matches = [
        (section, item)
        for section in ("fixed_commitments", "hobbies")
        for item in intake.get(section, [])
        if day in item["days"] and _matches_words(course_words, item["label"])
    ]
    if not study_matches and not commitment_matches:
        return {"status": "ok", "reply": f"I couldn't find a matching timetable item on {day}; nothing was changed."}

    labels = {block["label"] for block in study_matches}
    overrides = [
        override
        for override in intake.get("schedule_overrides", [])
        if override["label"] not in labels
    ]
    overrides.extend({"label": label, "excluded_day": day} for label in labels)
    updated_intake = {**intake, "schedule_overrides": overrides}

    for section in ("fixed_commitments", "hobbies"):
        selected_items = {
            id(item)
            for matched_section, item in commitment_matches
            if matched_section == section
        }
        if not selected_items:
            continue
        updated_items = []
        for item in updated_intake.get(section, []):
            if id(item) not in selected_items:
                updated_items.append(item)
                continue
            remaining_days = [item_day for item_day in item["days"] if item_day != day]
            if remaining_days:
                updated_items.append({**item, "days": remaining_days})
        updated_intake[section] = updated_items

    removed_labels = sorted(labels | {item["label"] for _, item in commitment_matches})
    if study_matches and not commitment_matches and len(labels) == 1:
        reply = f"Removed {removed_labels[0]} from {day}. Its deadline is still in your planner."
        action = "study_blocks_removed"
    elif len(removed_labels) == 1:
        reply = f"Removed {removed_labels[0]} from {day}."
        action = "schedule_items_removed"
    else:
        reply = f"Removed {', '.join(removed_labels)} from {day}."
        action = "schedule_items_removed"
    return _rebuild(updated_intake, reply, action)


def _change_scheduled_item(message):
    match = re.match(r"\s*(?:change|rename|replace|make|turn)\s+(.+?)\s*$", message, re.IGNORECASE)
    if not match:
        return None

    intake = get_intake()
    if not intake:
        return {"status": "ok", "reply": "I don't have planner details loaded yet."}

    parts = re.split(r"\s+to\s+", match.group(1).strip().rstrip(".!? "), flags=re.IGNORECASE)
    if len(parts) < 2:
        return None
    old_query = " to ".join(parts[:-1]).strip()
    new_label = parts[-1].strip()
    day_match = re.search(
        r"\s+on\s+(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\s*$",
        old_query,
        re.IGNORECASE,
    )
    day = DAYS[day_match.group(1).lower()] if day_match else None
    if day_match:
        old_query = old_query[:day_match.start()].strip()
    old_query = re.sub(r"\b(course|class|study|block|session|commitment|activity|the|my)\b", " ", old_query, flags=re.IGNORECASE)
    old_words = re.findall(r"[a-z0-9]+", old_query.lower())
    if not old_words:
        return {"status": "ok", "reply": "Which timetable item should I change?"}
    if not new_label:
        return {"status": "ok", "reply": "What should I change it to?"}
    if new_label.islower():
        new_label = new_label.title()

    candidates = []
    table = get_schedule() or {}
    for day_name, blocks in table.items():
        if day is not None and day_name != day:
            continue
        for block in blocks:
            if block["category"] == "Study" and _matches_words(old_words, block["label"]):
                candidates.append(("study", day_name, block, None))

    for section in ("fixed_commitments", "hobbies"):
        for item in intake.get(section, []):
            if not _matches_words(old_words, item["label"]):
                continue
            for item_day in item["days"]:
                if day is None or item_day == day:
                    candidates.append((section, item_day, item, section))

    if not candidates:
        day_context = f" on {day}" if day else " in your timetable"
        return {"status": "ok", "reply": f"I couldn't find {old_query.strip()} study blocks or commitments{day_context}; nothing was changed."}
    if len(candidates) > 1:
        options = "; ".join(f"{item_day}: {item['label']}" for _, item_day, item, _ in candidates[:4])
        return {"status": "ok", "reply": f"I found more than one match: {options}. Which day or block should I change?"}

    kind, selected_day, selected, section = candidates[0]
    if kind == "study":
        overrides = [
            override
            for override in intake.get("schedule_overrides", [])
            if override["label"] != selected["label"]
        ]
        overrides.append({"label": selected["label"], "excluded_day": selected_day})
        fixed_commitments = [
            *intake["fixed_commitments"],
            {
                "label": new_label,
                "days": [selected_day],
                "start": selected["start"],
                "end": selected["end"],
            },
        ]
        updated_intake = {
            **intake,
            "fixed_commitments": fixed_commitments,
            "schedule_overrides": overrides,
        }
        reply = (
            f"Changed {selected['label']} to {new_label} on {selected_day} "
            f"({selected['start']}–{selected['end']}). Its deadline remains in your planner."
        )
        return _rebuild(updated_intake, reply, "study_block_changed")

    updated_items = []
    for item in intake[section]:
        if item is not selected:
            updated_items.append(item)
            continue

        remaining_days = [item_day for item_day in item["days"] if item_day != selected_day]
        if remaining_days:
            updated_items.append({**item, "days": remaining_days})
        updated_items.append({**item, "label": new_label, "days": [selected_day]})

    updated_intake = {**intake, section: updated_items}
    reply = f"Changed {selected['label']} on {selected_day} to {new_label} ({selected['start']}–{selected['end']})."
    return _rebuild(updated_intake, reply, "commitment_renamed")


def _adjust_commitment_duration(message):
    match = DURATION_ADJUST_PATTERN.search(message)
    if not match:
        return None

    intake = get_intake()
    table = get_schedule()
    if not intake or not table:
        return {"status": "ok", "reply": "I don't have a timetable to adjust yet. Ask me to rebuild your week first."}

    action, target, day_text, amount_text = match.groups()
    day = DAYS[day_text.lower()] if day_text else None
    target = re.sub(r"\b(on|my|the|commitment|activity|hobby|event|block)\b", " ", target, flags=re.IGNORECASE)
    target_words = re.findall(r"[a-z0-9]+", target.lower())
    amount = int(amount_text)
    if not target_words or amount <= 0:
        return {"status": "ok", "reply": "Tell me which activity to change and by how many minutes."}

    candidates = []
    for section in ("fixed_commitments", "hobbies"):
        for item in intake.get(section, []):
            if not _matches_words(target_words, item["label"]):
                continue
            for item_day in item["days"]:
                if day is None or item_day == day:
                    candidates.append((section, item_day, item))

    if not candidates:
        day_context = f" on {day}" if day else ""
        return {"status": "ok", "reply": f"I couldn't find {target.strip()}{day_context} to adjust."}
    if len(candidates) > 1:
        options = "; ".join(f"{item_day}: {item['label']}" for _, item_day, item in candidates[:4])
        return {"status": "ok", "reply": f"I found more than one match: {options}. Which day should I adjust?"}

    section, selected_day, selected = candidates[0]
    category = "Fixed" if section == "fixed_commitments" else "Hobby"
    current_block = next((
        block for block in table[selected_day]
        if block["category"] == category
        and block["label"] == selected["label"]
        and block["start"] == selected["start"]
        and block["end"] == selected["end"]
    ), None)
    if current_block is None:
        return {"status": "ok", "reply": f"I couldn't find {selected['label']} on {selected_day} in the current timetable."}

    start_minutes = time_to_minutes(selected["start"])
    end_minutes = time_to_minutes(selected["end"])
    extending = action.lower() in ("extend", "lengthen", "increase")
    new_end = end_minutes + amount if extending else end_minutes - amount
    if new_end <= start_minutes:
        return {"status": "ok", "reply": "That change would leave no time for the activity. Choose a smaller reduction."}
    if new_end >= 24 * 60:
        return {"status": "ok", "reply": "That change would push the activity past midnight. Choose a smaller extension."}

    for other in table[selected_day]:
        if other is current_block:
            continue
        if start_minutes < time_to_minutes(other["end"]) and time_to_minutes(other["start"]) < new_end:
            return {"status": "ok", "reply": f"That would overlap with {other['label']} at {other['start']}–{other['end']}. Choose a smaller change."}

    updated_items = []
    for item in intake[section]:
        if item is not selected:
            updated_items.append(item)
            continue
        remaining_days = [item_day for item_day in item["days"] if item_day != selected_day]
        if remaining_days:
            updated_items.append({**item, "days": remaining_days})
        updated_items.append({
            **item,
            "days": [selected_day],
            "end": minutes_to_time(new_end),
        })

    updated_intake = {**intake, section: updated_items}
    verb = "Extended" if extending else "Shortened"
    reply = f"{verb} {selected['label']} on {selected_day} by {amount} minutes, to {minutes_to_time(new_end)}."
    return _rebuild(updated_intake, reply, "duration_adjusted")


def handle_agent_message(message):
    intake = get_intake()
    if not intake:
        return {"status": "ok", "reply": "I don't have planner details loaded yet. Open planner details or ask me to use the sample plan."}

    duration_action = _adjust_commitment_duration(message)
    if duration_action:
        return duration_action

    preference_action = _change_preferences(message, intake)
    if preference_action:
        return preference_action

    deadline_action = _add_deadline(message, intake)
    if deadline_action:
        return deadline_action

    lower = message.lower()
    if any(word in lower for word in ("overwhelmed", "overwhelm", "too packed", "lighter")):
        return _change_preferences("", intake)

    if any(word in lower for word in ("rebuild", "regenerate", "refresh timetable", "refresh schedule")):
        return _rebuild(intake, "Done. I rebuilt your timetable from the current planner details.", "schedule_rebuilt")

    change_action = _change_scheduled_item(message)
    if change_action:
        return change_action

    remove_action = _remove_study_blocks(message)
    if remove_action:
        return remove_action

    move_action = _move_study_block(message)
    if move_action:
        return move_action

    if "deadline" in lower or "due" in lower:
        return {"status": "ok", "reply": generate_reply(message, get_schedule())}

    return {
        "status": "ok",
        "reply": "I can update session lengths, deadlines, study blocks, and commitments. For example: “make sessions 40 minutes,” “remove Calculus II on Tuesday,” or “change Job on Saturday to Sleep.”",
    }