# ---------- PHASE 5: /generate-schedule and /schedule ROUTES ----------

from flask import Blueprint, jsonify
from storage.db import get_intake, save_schedule, get_schedule
from logic.planning import create_weekly_schedule

schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/generate-schedule", methods=["POST"])
def generate_schedule():
    intake = get_intake()
    if not intake:
        return jsonify({"status": "error", "message": "No intake data found"}), 400

    weekly_table = create_weekly_schedule(intake)

    save_schedule(weekly_table)
    return jsonify({"status": "ok", "weekly_table": weekly_table}), 200


@schedule_bp.route("/schedule", methods=["GET"])
def fetch_schedule():
    weekly_table = get_schedule()
    if not weekly_table:
        return jsonify({"status": "error", "message": "No schedule generated yet"}), 404

    return jsonify({"status": "ok", "weekly_table": weekly_table}), 200