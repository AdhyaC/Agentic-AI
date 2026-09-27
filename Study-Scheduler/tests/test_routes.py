# ---------- PHASE 7: API ROUTE TESTS ----------

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


VALID_INTAKE = {
    "courses": [{"name": "Calc II", "credits": 4, "difficulty": "High"}],
    "deadlines": [
        {"course": "Calc II", "task": "Midterm", "type": "Exam", "date": "2026-12-01"}
    ],
    "fixed_commitments": [
        {"label": "Class", "days": ["Mon"], "start": "09:00", "end": "12:00"}
    ],
    "available_study_hours": [
        {"days": ["Mon"], "start": "13:00", "end": "17:00"}
    ],
    "hobbies": [
        {"label": "Gym", "days": ["Mon"], "start": "18:00", "end": "19:00"}
    ],
    "preferences": {"session_length_minutes": 50, "break_length_minutes": 10},
}


def test_intake_rejects_missing_fields(client):
    response = client.post("/intake", json={"courses": []})
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_mock_data_returns_complete_intake(client):
    response = client.get("/mock-data")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert len(body["intake"]["courses"]) > 0
    assert len(body["intake"]["deadlines"]) > 0


def test_intake_accepts_valid_payload(client):
    response = client.post("/intake", json=VALID_INTAKE)
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_generate_schedule_requires_intake_first(client):
    # Fresh client with nothing submitted yet would 400,
    # but since storage is module-level, submit intake first for isolation
    client.post("/intake", json=VALID_INTAKE)
    response = client.post("/generate-schedule")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert "weekly_table" in body


def test_fetch_schedule_after_generation(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.get("/schedule")
    assert response.status_code == 200
    assert "weekly_table" in response.get_json()


def test_reminders_requires_schedule(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.get("/reminders")
    assert response.status_code == 200
    body = response.get_json()
    assert "reminders" in body
    assert "upcoming_deadlines" in body["reminders"]


def test_feedback_updates_preferences(client):
    client.post("/intake", json=VALID_INTAKE)
    feedback_payload = {"felt_too_packed": True}
    response = client.post("/feedback", json=feedback_payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["updated_preferences"]["break_length_minutes"] > 10


def test_coach_reply_handles_reschedule_request(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "move it to 11am"})
    assert response.status_code == 200
    body = response.get_json()
    assert "11" in body["reply"]
    assert "outside your available study hours" in body["reply"]


def test_coach_changes_session_length_and_rebuilds(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "make sessions 40 minutes"})

    body = response.get_json()
    assert body["action"] == "preferences_updated"
    assert body["intake"]["preferences"]["session_length_minutes"] == 40
    study_blocks = [
        block
        for day in body["weekly_table"].values()
        for block in day
        if block["category"] == "Study"
    ]
    assert study_blocks
    assert study_blocks[0]["end"] == "13:40"


def test_coach_adds_deadline_and_rebuilds(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "add a deadline for Calc II: Final Exam, due 2026-12-15"
    })

    body = response.get_json()
    assert body["action"] == "deadline_added"
    assert body["intake"]["deadlines"][-1]["task"] == "Final Exam"
    assert any(
        block["label"] == "Calc II — Final Exam"
        for day in body["weekly_table"].values()
        for block in day
    )


def test_coach_moves_matching_block_to_available_time(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "move Calc II Midterm to 14:00"
    })

    body = response.get_json()
    assert body["action"] == "study_block_moved"
    moved_block = next(
        block for block in body["weekly_table"]["Mon"]
        if block["category"] == "Study"
    )
    assert moved_block["start"] == "14:00"


def test_coach_keeps_moved_block_after_later_rebuild(client):
    client.post("/intake", json=VALID_INTAKE)
    client.post("/generate-schedule")
    client.post("/coach-reply", json={"message": "move Calc II Midterm to 14:00"})
    response = client.post("/coach-reply", json={"message": "make sessions 40 minutes"})

    moved_block = next(
        block for block in response.get_json()["weekly_table"]["Mon"]
        if block["category"] == "Study"
    )
    assert moved_block["start"] == "14:00"
    assert moved_block["end"] == "14:40"


def test_coach_removes_course_block_from_day_but_keeps_deadline(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "remove calculus-II on Tuesday"})

    body = response.get_json()
    assert body["action"] == "study_blocks_removed"
    assert not any(
        block["category"] == "Study" and "Calculus II" in block["label"]
        for block in body["weekly_table"]["Tue"]
    )
    assert any(deadline["course"] == "Calculus II" for deadline in body["intake"]["deadlines"])

    rebuilt = client.post("/coach-reply", json={"message": "make sessions 40 minutes"}).get_json()
    assert not any(
        block["category"] == "Study" and "Calculus II" in block["label"]
        for block in rebuilt["weekly_table"]["Tue"]
    )


def test_coach_changes_only_saturday_commitment_label(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "change job on Saturday to Sleep"})

    body = response.get_json()
    assert body["action"] == "commitment_renamed"
    assert any(
        item["label"] == "Sleep"
        and item["days"] == ["Sat"]
        and item["start"] == "09:00"
        and item["end"] == "13:00"
        for item in body["intake"]["fixed_commitments"]
    )
    assert any(
        item["label"] == "Job (Library)" and item["days"] == ["Tue", "Thu"]
        for item in body["intake"]["fixed_commitments"]
    )
    assert any(
        block["label"] == "Sleep" and block["start"] == "09:00"
        for block in body["weekly_table"]["Sat"]
    )


def test_coach_removes_course_with_small_spelling_error(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "remove Organic Chemisty on Thursday"
    })

    body = response.get_json()
    assert body["action"] == "study_blocks_removed"
    assert not any(
        block["category"] == "Study" and "Organic Chemistry" in block["label"]
        for block in body["weekly_table"]["Thu"]
    )


def test_coach_removes_recurring_hobby_from_one_day_only(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "remove gym on friday"})

    body = response.get_json()
    assert body["action"] == "schedule_items_removed"
    assert not any(block["category"] == "Hobby" and block["label"] == "Gym" for block in body["weekly_table"]["Fri"])
    gym = next(item for item in body["intake"]["hobbies"] if item["label"] == "Gym")
    assert gym["days"] == ["Mon", "Wed"]


def test_coach_removes_single_day_hobby(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={"message": "remove call family on sun"})

    body = response.get_json()
    assert body["action"] == "schedule_items_removed"
    assert not any(item["label"] == "Call Family" for item in body["intake"]["hobbies"])
    assert not any(block["label"] == "Call Family" for block in body["weekly_table"]["Sun"])


def test_coach_asks_which_day_for_ambiguous_course_change(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "change Intro to Statistics to sleep"
    })

    body = response.get_json()
    assert "more than one match" in body["reply"]
    assert "Mon:" in body["reply"]
    assert "Sat" in body["reply"]


def test_coach_changes_a_course_study_block_to_sleep(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "make Intro to Statistics on Saturday to sleep"
    })

    body = response.get_json()
    assert body["action"] == "study_block_changed"
    assert any(
        item["label"] == "Sleep" and item["days"] == ["Sat"]
        for item in body["intake"]["fixed_commitments"]
    )
    assert any(deadline["course"] == "Intro to Statistics" for deadline in body["intake"]["deadlines"])
    assert any(
        block["category"] == "Fixed" and block["label"] == "Sleep"
        for block in body["weekly_table"]["Sat"]
    )


def test_coach_changes_spanish_study_block_on_requested_day(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")
    response = client.post("/coach-reply", json={
        "message": "change spanish III on friday to sleep"
    })

    body = response.get_json()
    assert body["action"] == "study_block_changed"
    assert any(
        block["category"] == "Fixed" and block["label"] == "Sleep"
        for block in body["weekly_table"]["Fri"]
    )

    rebuilt = client.post("/coach-reply", json={"message": "make sessions 40 minutes"}).get_json()
    assert any(
        block["category"] == "Fixed" and block["label"] == "Sleep"
        for block in rebuilt["weekly_table"]["Fri"]
    )
    assert not any(
        block["category"] == "Study" and "Spanish III" in block["label"]
        for block in rebuilt["weekly_table"]["Fri"]
    )


def test_coach_extends_and_reduces_hobby_duration(client):
    intake = client.get("/mock-data").get_json()["intake"]
    client.post("/intake", json=intake)
    client.post("/generate-schedule")

    extended = client.post("/coach-reply", json={
        "message": "extend guitar practice on sunday by 30 mins"
    }).get_json()
    assert extended["action"] == "duration_adjusted"
    guitar = next(item for item in extended["intake"]["hobbies"] if item["label"] == "Guitar Practice")
    assert guitar["start"] == "16:00"
    assert guitar["end"] == "17:30"

    reduced = client.post("/coach-reply", json={
        "message": "reduce guitar practice on sunday by 15 minutes"
    }).get_json()
    guitar = next(item for item in reduced["intake"]["hobbies"] if item["label"] == "Guitar Practice")
    assert guitar["start"] == "16:00"
    assert guitar["end"] == "17:15"


def test_coach_reply_rejects_empty_message(client):
    response = client.post("/coach-reply", json={"message": ""})
    assert response.status_code == 400