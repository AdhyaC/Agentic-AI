# ---------- PHASE 5: /intake ROUTE ----------

from flask import Blueprint, request, jsonify
import mock_data
from models.schemas import validate_intake_payload
from storage.db import save_intake

intake_bp = Blueprint("intake", __name__)


@intake_bp.route("/mock-data", methods=["GET"])
def get_mock_data():
    return jsonify({
        "status": "ok",
        "intake": {
            "courses": mock_data.courses,
            "deadlines": mock_data.deadlines,
            "fixed_commitments": mock_data.fixed_commitments,
            "available_study_hours": mock_data.available_study_hours,
            "hobbies": mock_data.hobbies,
            "preferences": mock_data.preferences,
        },
    }), 200


@intake_bp.route("/intake", methods=["POST"])
def submit_intake():
    payload = request.get_json()

    errors = validate_intake_payload(payload)
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

    save_intake(payload)
    return jsonify({"status": "ok", "message": "Intake data saved"}), 200