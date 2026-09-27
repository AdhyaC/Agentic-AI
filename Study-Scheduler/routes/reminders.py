# ---------- PHASE 5: /reminders ROUTE ----------

from flask import Blueprint, jsonify
from storage.db import get_schedule, get_deadlines
from logic.reminders import build_reminder_summary
from datetime import date

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("/reminders", methods=["GET"])
def fetch_reminders():
    weekly_table = get_schedule()
    deadlines = get_deadlines()

    if not weekly_table:
        return jsonify({"status": "error", "message": "No schedule generated yet"}), 404

    today_str = date.today().isoformat()
    summary = build_reminder_summary(deadlines, weekly_table, today_str)

    return jsonify({"status": "ok", "reminders": summary}), 200