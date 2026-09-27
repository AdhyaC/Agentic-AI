const BASE_URL = "http://localhost:5000";

export async function fetchMockData() {
  const res = await fetch(`${BASE_URL}/mock-data`);
  return res.json();
}

export async function submitIntake(data) {
  const res = await fetch(`${BASE_URL}/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function generateSchedule() {
  const res = await fetch(`${BASE_URL}/generate-schedule`, { method: "POST" });
  return res.json();
}

export async function fetchSchedule() {
  const res = await fetch(`${BASE_URL}/schedule`);
  return res.json();
}

export async function fetchReminders() {
  const res = await fetch(`${BASE_URL}/reminders`);
  return res.json();
}

export async function submitFeedback(feedback) {
  const res = await fetch(`${BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedback),
  });
  return res.json();
}

export async function sendCoachMessage(message) {
  const res = await fetch(`${BASE_URL}/coach-reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return res.json();
}