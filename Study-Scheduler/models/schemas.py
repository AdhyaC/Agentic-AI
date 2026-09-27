# ---------- PHASE 5: DATA MODELS / VALIDATION ----------
# Lightweight validation helpers for incoming intake data.
# Kept simple (dict checks) rather than a heavy validation library,
# matching the project's "no complex tooling" constraint.

REQUIRED_COURSE_FIELDS = {"name", "credits", "difficulty"}
REQUIRED_DEADLINE_FIELDS = {"course", "task", "type", "date"}
REQUIRED_COMMITMENT_FIELDS = {"label", "days", "start", "end"}


def validate_intake_payload(payload):
    errors = []

    for field in ["courses", "deadlines", "fixed_commitments",
                  "available_study_hours", "hobbies", "preferences"]:
        if field not in payload:
            errors.append(f"Missing field: {field}")

    if errors:
        return errors

    for c in payload["courses"]:
        if not REQUIRED_COURSE_FIELDS.issubset(c.keys()):
            errors.append(f"Invalid course entry: {c}")

    for d in payload["deadlines"]:
        if not REQUIRED_DEADLINE_FIELDS.issubset(d.keys()):
            errors.append(f"Invalid deadline entry: {d}")

    for c in payload["fixed_commitments"] + payload["hobbies"]:
        if not REQUIRED_COMMITMENT_FIELDS.issubset(c.keys()):
            errors.append(f"Invalid commitment/hobby entry: {c}")

    return errors