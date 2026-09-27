# ---------- /coach-reply ROUTE ----------

from flask import Blueprint, request, jsonify
from logic.coach import handle_agent_message

coach_bp = Blueprint("coach", __name__)


@coach_bp.route("/coach-reply", methods=["POST"])
def coach_reply():
    payload = request.get_json()
    message = payload.get("message", "") if payload else ""

    if not message.strip():
        return jsonify({"status": "error", "message": "No message provided"}), 400

    return jsonify(handle_agent_message(message)), 200