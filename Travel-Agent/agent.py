import json
from datetime import date, datetime, timedelta

from llm import call_llm
from memory import load_preferences, save_preferences
from tools import search_flights, search_hotels, book_trip

REQUIRED = ["origin", "destination", "start_date", "nights"]

QUESTIONS = {
    "origin": "Which city are you flying from?",
    "destination": "Where do you want to go?",
    "start_date": "What date do you want to leave? (e.g. 2026-12-20)",
    "nights": "How many nights will you stay?",
}

ALLOWED_TOOLS = ["search_flights", "search_hotels", "book_trip"]

DEFAULT_PLAN = [
    {"tool": "search_flights", "why": "Find flights to the destination"},
    {"tool": "search_hotels", "why": "Find hotels for the stay"},
    {"tool": "book_trip", "why": "Book the best option after human approval"},
]

MAX_RETRIES = 2


def log(label, message):
    print(f"[{label}] {message}")


def _ask_json(prompt):
    try:
        data = json.loads(call_llm(prompt, json_mode=True))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# PHASE 3: Goal, Planning, Reasoning
# ---------------------------------------------------------------------------
def parse_goal(user_text, goal=None):
    goal = dict(goal or {})

    prompt = f"""Today's date is {date.today()}.
Extract travel details from the user's message. Reply with JSON only, using exactly these keys:
{{"origin": string or null, "destination": string or null,
  "start_date": "YYYY-MM-DD" or null, "nights": integer or null,
  "travelers": integer or null, "budget": number or null,
  "preferences": object}}
Rules:
- Use null for anything the user did not say. Do not guess.
- budget is the total trip budget in INR for all travelers.
- preferences holds lasting preferences the user states, for example
  {{"hotel_style": "boutique", "airline": "IndiGo", "seat": "window"}}.
  Use an empty object if there are none.
Already known: {json.dumps(goal)}
User message: {user_text}"""

    data = _ask_json(prompt)

    for key in ["origin", "destination", "start_date", "nights", "travelers", "budget"]:
        if data.get(key) is not None:
            goal[key] = data[key]

    for key in ["nights", "travelers"]:
        if key in goal:
            try:
                goal[key] = int(goal[key])
            except (ValueError, TypeError):
                del goal[key]
    if "start_date" in goal:
        try:
            datetime.strptime(str(goal["start_date"]), "%Y-%m-%d")
        except ValueError:
            del goal["start_date"]

    new_prefs = data.get("preferences") or {}
    if isinstance(new_prefs, dict) and new_prefs:
        save_preferences(new_prefs)
    if data.get("budget") is not None:
        save_preferences({"budget": data["budget"]})

    goal.setdefault("travelers", 1)
    if "budget" not in goal:
        remembered = load_preferences().get("budget")
        if remembered:
            goal["budget"] = remembered

    missing = [k for k in REQUIRED if not goal.get(k)]
    return goal, missing


def make_plan(goal):
    prompt = f"""You are planning a trip booking for this goal: {json.dumps(goal)}
Available tools: search_flights, search_hotels, book_trip.
Reply with JSON only in this shape:
{{"steps": [{{"tool": "<tool name>", "why": "<short reason>"}}]}}
Search flights and hotels first, and book_trip last. Use each tool once."""

    steps = _ask_json(prompt).get("steps", [])
    steps = [s for s in steps if isinstance(s, dict) and s.get("tool") in ALLOWED_TOOLS]
    tools_used = [s["tool"] for s in steps]

    if set(tools_used) != set(ALLOWED_TOOLS) or tools_used[-1] != "book_trip":
        return DEFAULT_PLAN
    return steps


def reason_over_options(goal, flights, hotels):
    if not flights or not hotels:
        return None

    prefs = load_preferences()
    travelers = goal.get("travelers", 1)

    prompt = f"""You are a travel agent choosing the best trip.
Goal: {json.dumps(goal)}
Remembered preferences: {json.dumps(prefs)}
Flights (price is per person): {json.dumps(flights)}
Hotels (total is for the whole stay): {json.dumps(hotels)}
Number of travelers: {travelers}
Total cost = flight price x travelers + hotel total. Prefer options that fit the budget
and match the remembered preferences.
Reply with JSON only: {{"flight_id": "<id>", "hotel_id": "<id>", "explanation": "<2 short sentences>"}}
In the explanation, refer to options by airline and hotel name, never by id."""

    pick = _ask_json(prompt)
    flight = next((f for f in flights if f["id"] == pick.get("flight_id")), None)
    hotel = next((h for h in hotels if h["id"] == pick.get("hotel_id")), None)

    explanation = pick.get("explanation", "")
    if flight is None or hotel is None:
        flight = min(flights, key=lambda f: f["price"])
        hotel = min(hotels, key=lambda h: h["total"])
        explanation = "Picked the cheapest flight and hotel."

    total = flight["price"] * travelers + hotel["total"]
    budget = goal.get("budget")
    return {
        "flight": flight,
        "hotel": hotel,
        "total": total,
        "within_budget": budget is None or total <= budget,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# PHASE 4: Lifecycle loop (autonomy + re-planning)
# ---------------------------------------------------------------------------
def run_tool(name, goal):
    if name == "search_flights":
        return search_flights(goal["origin"], goal["destination"], goal["start_date"])
    if name == "search_hotels":
        return search_hotels(goal["destination"], goal["start_date"], goal["nights"])
    raise ValueError(f"Unknown tool: {name}")


def adjust_goal(goal, reason, attempt):
    """Return (new_goal, description). Never writes to saved preferences."""
    new_goal = dict(goal)

    # No results: shift the date. Over budget: shift the date first, then relax the budget.
    if reason == "no_results" or attempt == 1 or not goal.get("budget"):
        old = goal["start_date"]
        shifted = datetime.strptime(old, "%Y-%m-%d").date() + timedelta(days=1)
        new_goal["start_date"] = shifted.isoformat()
        return new_goal, f"shifting start date {old} -> {new_goal['start_date']}"

    old_budget = goal["budget"]
    new_goal["budget"] = round(old_budget * 1.15)
    return new_goal, f"raising budget {old_budget} -> {new_goal['budget']} INR (+15%)"


def run_agent(goal):
    state = {
        "goal": goal,
        "plan": make_plan(goal),
        "observations": [],
        "retries": 0,
        "recommendation": None,
        "original_budget": goal.get("budget"),
        "booking": None,
        "status": "running",
    }

    log("GOAL", json.dumps(goal))
    for i, step in enumerate(state["plan"], 1):
        log("PLAN", f"{i}. {step['tool']} - {step['why']}")

    while True:
        goal = state["goal"]
        results = {}

        for step in state["plan"]:
            tool = step["tool"]
            if tool == "book_trip":
                continue  # booking only happens in approve(), after human approval
            log("ACTION", f"{tool} ({step['why']})")
            output = run_tool(tool, goal)
            results[tool] = output
            state["observations"].append({"tool": tool, "count": len(output)})
            log("OBSERVATION", f"{tool} returned {len(output)} result(s)")

        flights = results.get("search_flights", [])
        hotels = results.get("search_hotels", [])
        recommendation = reason_over_options(goal, flights, hotels)

        if recommendation is None:
            failure = "no_results"
        elif not recommendation["within_budget"]:
            failure = "over_budget"
        else:
            failure = None

        if failure is None:
            state["recommendation"] = recommendation
            state["status"] = "awaiting_approval"
            log("RESULT", "Found an option that fits the goal.")
            return state

        log("OBSERVATION", f"Problem: {failure.replace('_', ' ')}")

        if state["retries"] >= MAX_RETRIES:
            state["recommendation"] = recommendation
            if recommendation is None:
                state["status"] = "failed"
                log("RESULT", f"Gave up after {MAX_RETRIES} retries: no options found.")
            else:
                state["status"] = "awaiting_approval"
                log("RESULT", f"Gave up after {MAX_RETRIES} retries: best option is still over budget.")
            return state

        state["retries"] += 1
        state["goal"], change = adjust_goal(goal, failure, state["retries"])
        log("RE-PLAN", f"Retry {state['retries']}/{MAX_RETRIES}: {change}")


# ---------------------------------------------------------------------------
# PHASE 5: Human approval
# ---------------------------------------------------------------------------
def approval_summary(state):
    rec = state["recommendation"]
    goal = state["goal"]
    lines = [
        "Please review this trip:",
        f"  Route:  {goal['origin']} -> {goal['destination']} on {goal['start_date']}, {goal['nights']} night(s)",
        f"  Flight: {rec['flight']['airline']} {rec['flight']['flight_no']}",
        f"  Hotel:  {rec['hotel']['name']}",
        f"  Total:  {rec['total']} INR for {goal['travelers']} traveler(s)",
    ]
    original = state["original_budget"]
    if original is not None:
        if rec["within_budget"]:
            lines.append(f"  Budget: {goal['budget']} INR (within budget)")
            if goal["budget"] != original:
                lines.append(f"  Note:   budget was raised from {original} to {goal['budget']} INR during re-planning")
        else:
            lines.append(f"  Budget: OVER BUDGET (your budget {original} INR, agent tried up to {goal['budget']} INR)")
    return "\n".join(lines)


def _do_booking(state):
    rec = state["recommendation"]
    # SWAP IN REAL API HERE: this calls the mock book_trip in tools.py
    return book_trip(rec["flight"], rec["hotel"], travelers=state["goal"]["travelers"])


def approve(state):
    if state["status"] != "awaiting_approval":
        log("APPROVAL", f"Refused: cannot approve while status is '{state['status']}'.")
        return state
    log("APPROVAL", "Approved by user.")
    log("ACTION", "book_trip")
    state["booking"] = _do_booking(state)
    state["status"] = "booked"
    log("OBSERVATION", f"book_trip returned: {state['booking']}")
    return state


def reject(state):
    if state["status"] != "awaiting_approval":
        log("APPROVAL", f"Refused: cannot reject while status is '{state['status']}'.")
        return state
    state["status"] = "rejected"
    log("APPROVAL", "Rejected by user. Nothing was booked.")
    return state


# ---------------------------------------------------------------------------
# Run from the terminal: python agent.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    goal = {}
    text = input("You: ")
    while True:
        goal, missing = parse_goal(text, goal)
        if not missing:
            break
        text = input("Agent: " + " ".join(QUESTIONS[m] for m in missing) + "\nYou: ")

    state = run_agent(goal)
    print("\nSTATUS:", state["status"], "| retries used:", state["retries"])

    if state["status"] == "awaiting_approval":
        print("\n" + approval_summary(state))
        print("  Why:   ", state["recommendation"]["explanation"])
        answer = input("\nApprove booking? (approve/reject): ").strip().lower()
        if answer == "approve":
            approve(state)
        else:
            reject(state)
        print("FINAL STATUS:", state["status"], "| booking:", state["booking"])
    else:
        print("No bookable option found. Nothing was booked.")