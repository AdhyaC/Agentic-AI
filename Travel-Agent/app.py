import io
import re
import uuid
from contextlib import redirect_stdout
from threading import Lock

from flask import Flask, jsonify, render_template, request, session

import agent

app = Flask(__name__)
app.secret_key = "change-this-in-real-use"

SESSIONS = {}  # sid -> {"goal": {...}, "state": None or agent state}
LOCK = Lock()  # stdout capture is global, so handle one request at a time
LINE = re.compile(r"^\[([A-Z\-]+)\] (.*)$")


def get_session():
    sid = session.get("sid")
    if sid not in SESSIONS:
        sid = uuid.uuid4().hex
        session["sid"] = sid
        SESSIONS[sid] = {"goal": {}, "state": None}
    return SESSIONS[sid]


def capture(fn, *args):
    """Run fn, return (result, lifecycle lines printed by the agent)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*args)
    lines = []
    for raw in buf.getvalue().splitlines():
        m = LINE.match(raw)
        if m:
            lines.append({"label": m.group(1), "text": m.group(2)})
    return result, lines


def approval_details(state):
    goal = state["goal"]
    recommendation = state["recommendation"]
    flight = recommendation["flight"]
    hotel = recommendation["hotel"]
    return {
        "origin": goal["origin"],
        "destination": goal["destination"],
        "start_date": goal["start_date"],
        "nights": goal["nights"],
        "flight": f'{flight["airline"]} {flight["flight_no"]}',
        "departure": flight["depart"],
        "hotel": hotel["name"],
        "total": recommendation["total"],
        "travelers": goal["travelers"],
        "budget": state["original_budget"],
        "within_budget": recommendation["within_budget"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    text = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not text:
        return jsonify({"reply": "Please type a message.", "lines": [], "approval": False})

    with LOCK:
        sess = get_session()

        if sess["state"] and sess["state"]["status"] == "awaiting_approval":
            return jsonify({
                "reply": "A trip is waiting for your decision. Please use Approve or Reject.",
                "lines": [], "approval": True,
                "summary": agent.approval_summary(sess["state"]),
                "trip": approval_details(sess["state"]),
            })

        goal, missing = agent.parse_goal(text, sess["goal"])
        sess["goal"] = goal

        if missing:
            return jsonify({
                "reply": " ".join(agent.QUESTIONS[m] for m in missing),
                "lines": [{"label": "GOAL", "text": "Missing details: " + ", ".join(missing)}],
                "approval": False,
            })

        state, lines = capture(agent.run_agent, dict(goal))
        sess["state"] = state

        if state["status"] == "awaiting_approval":
            return jsonify({
                "reply": state["recommendation"]["explanation"],
                "lines": lines, "approval": True,
                "summary": agent.approval_summary(state),
                "trip": approval_details(state),
            })

        sess["goal"], sess["state"] = {}, None
        return jsonify({
            "reply": "Sorry, I couldn't find a bookable option, even after adjusting. Nothing was booked. Send a new request to try again.",
            "lines": lines, "approval": False,
        })


@app.route("/pending-approval", methods=["GET"])
def pending_approval():
    with LOCK:
        state = get_session()["state"]
        if not state or state["status"] != "awaiting_approval":
            return jsonify({"approval": False})

        return jsonify({
            "approval": True,
            "summary": agent.approval_summary(state),
            "trip": approval_details(state),
        })


@app.route("/approve", methods=["POST"])
def approve():
    decision = (request.get_json(silent=True) or {}).get("decision")

    with LOCK:
        sess = get_session()
        state = sess["state"]
        if not state or state["status"] != "awaiting_approval":
            return jsonify({"reply": "There is nothing waiting for approval.", "lines": [], "approval": False})

        if decision == "approve":
            _, lines = capture(agent.approve, state)
            b = state["booking"]
            reply = (f"Booked! Confirmation {b['confirmation_id']}: {b['flight']} + {b['hotel']}, "
                     f"{b['total_cost']} {b['currency']}.")
        else:
            _, lines = capture(agent.reject, state)
            reply = "Rejected. Nothing was booked. Send a new request whenever you like."

        sess["goal"], sess["state"] = {}, None
        return jsonify({"reply": reply, "lines": lines, "approval": False})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)