# ---------- PHASE 6: /feedback ROUTE ----------

from flask import Blueprint, request, jsonify
from storage.db import (
    get_preferences,
    update_preferences,
    save_feedback_record,
    get_feedback_history,
)
from logic.feedback import apply_feedback, build_feedback_record
from datetime import date

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    payload = request.get_json()

    if not payload:
        return jsonify({"status": "error", "message": "No feedback data provided"}), 400

    current_preferences = get_preferences()
    updated_preferences = apply_feedback(current_preferences, payload)
    update_preferences(updated_preferences)

    record = build_feedback_record(
        week_of=date.today().isoformat(),
        feedback=payload,
        updated_preferences=updated_preferences,
    )
    save_feedback_record(record)

    return jsonify({
        "status": "ok",
        "updated_preferences": updated_preferences,
        "message": "Feedback applied — next schedule will reflect these changes"
    }), 200


@feedback_bp.route("/feedback-history", methods=["GET"])
def feedback_history():
    return jsonify({"status": "ok", "history": get_feedback_history()}), 200