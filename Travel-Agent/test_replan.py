import agent

real_search = agent.search_flights
calls = {"n": 0}

def flaky_search(*args, **kwargs):
    calls["n"] += 1
    return [] if calls["n"] == 1 else real_search(*args, **kwargs)

agent.search_flights = flaky_search

state = agent.run_agent({
    "origin": "Bengaluru", "destination": "Goa",
    "start_date": "2026-12-20", "nights": 3,
    "travelers": 2, "budget": 100000,
})
print("\nFINAL:", state["status"], "| retries:", state["retries"], "| date used:", state["goal"]["start_date"])