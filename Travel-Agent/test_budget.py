import agent

state = agent.run_agent({
    "origin": "Bengaluru", "destination": "Goa",
    "start_date": "2026-12-20", "nights": 3,
    "travelers": 2, "budget": 1000,
})
print("\nFINAL:", state["status"], "| retries:", state["retries"], "| budget used:", state["goal"]["budget"])