# ---------- PHASE 7: SCHEDULER LOGIC TESTS ----------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from logic.scheduler import (
    days_until,
    prioritize_deadlines,
    time_to_minutes,
    minutes_to_time,
    get_free_slots,
    allocate_sessions,
)


def test_days_until_future_date():
    assert days_until("2026-10-01", "2026-09-27") == 4


def test_days_until_past_date():
    assert days_until("2026-09-20", "2026-09-27") == -7


def test_days_until_same_day():
    assert days_until("2026-09-27", "2026-09-27") == 0


def test_prioritize_deadlines_orders_by_urgency():
    deadlines = [
        {"course": "A", "task": "Quiz", "type": "Quiz", "date": "2026-10-05"},
        {"course": "B", "task": "Midterm", "type": "Exam", "date": "2026-10-05"},
    ]
    result = prioritize_deadlines(deadlines, "2026-09-27")
    # Exam should be prioritized over Quiz at the same distance
    assert result[0]["task"] == "Midterm"


def test_prioritize_deadlines_skips_past_dates():
    deadlines = [
        {"course": "A", "task": "Old Quiz", "type": "Quiz", "date": "2026-09-01"},
        {"course": "B", "task": "Upcoming Exam", "type": "Exam", "date": "2026-10-05"},
    ]
    result = prioritize_deadlines(deadlines, "2026-09-27")
    assert len(result) == 1
    assert result[0]["task"] == "Upcoming Exam"


def test_time_to_minutes():
    assert time_to_minutes("09:30") == 570
    assert time_to_minutes("00:00") == 0
    assert time_to_minutes("23:59") == 1439


def test_minutes_to_time():
    assert minutes_to_time(570) == "09:30"
    assert minutes_to_time(0) == "00:00"


def test_time_conversion_roundtrip():
    for t in ["09:00", "13:45", "23:59"]:
        assert minutes_to_time(time_to_minutes(t)) == t


def test_get_free_slots_subtracts_commitments():
    available = [{"days": ["Mon"], "start": "09:00", "end": "17:00"}]
    commitments = [{"label": "Class", "days": ["Mon"], "start": "12:00", "end": "13:00"}]
    hobbies = []

    result = get_free_slots(available, commitments, hobbies)
    mon_slots = result["Mon"]

    # Should split into two segments around the class block
    assert (time_to_minutes("09:00"), time_to_minutes("12:00")) in mon_slots
    assert (time_to_minutes("13:00"), time_to_minutes("17:00")) in mon_slots


def test_allocate_sessions_respects_session_length():
    prioritized = [
        {"course": "Calc", "task": "Study", "date": "2026-10-01",
         "type": "Exam", "priority_score": 1, "days_left": 4},
    ]
    free_slots = {"Mon": [(540, 600)], "Tue": [], "Wed": [], "Thu": [],
                  "Fri": [], "Sat": [], "Sun": []}
    preferences = {"session_length_minutes": 50, "break_length_minutes": 10}

    schedule = allocate_sessions(prioritized, free_slots, preferences)
    assert len(schedule["Mon"]) == 1
    assert schedule["Mon"][0]["start"] == "09:00"
    assert schedule["Mon"][0]["end"] == "09:50"


def test_allocate_sessions_skips_too_small_slots():
    prioritized = [
        {"course": "Calc", "task": "Study", "date": "2026-10-01",
         "type": "Exam", "priority_score": 1, "days_left": 4},
    ]
    # Only a 20-minute slot available — too small for a 50-minute session
    free_slots = {"Mon": [(540, 560)], "Tue": [], "Wed": [], "Thu": [],
                  "Fri": [], "Sat": [], "Sun": []}
    preferences = {"session_length_minutes": 50, "break_length_minutes": 10}

    schedule = allocate_sessions(prioritized, free_slots, preferences)
    assert len(schedule["Mon"]) == 0