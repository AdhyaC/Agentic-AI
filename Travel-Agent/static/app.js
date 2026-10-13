/* ---------- Placeholder art (inline SVG, no image files) ---------- */
let gid = 0;
function scene(kind) {
  const id = "g" + (++gid);
  const sky = {
    beach: ["#bfe3f7", "#fdf3dc"], city: ["#a9d4f2", "#e8f3fb"], temple: ["#cfe8f8", "#fbefd9"],
    pool: ["#b6dcf3", "#eaf6fd"], hero: ["#9fd0f0", "#eef7fd"]
  }[kind];
  let shapes = "";
  if (kind === "beach") {
    shapes = `<circle cx="300" cy="80" r="34" fill="#ffd978"/>
      <rect y="150" width="400" height="60" fill="#2f80c8"/>
      <path d="M0 165 Q50 155 100 165 T200 165 T300 165 T400 165 V210 H0Z" fill="#4a9ad8"/>
      <path d="M0 200 Q120 180 240 205 T400 195 V260 H0Z" fill="#f3dfae"/>
      <path d="M70 215 L74 150" stroke="#6b4a2b" stroke-width="5"/>
      <path d="M74 150 Q50 135 30 150 M74 150 Q95 130 120 145 M74 150 Q70 125 80 118" stroke="#4c8a1f" stroke-width="5" fill="none" stroke-linecap="round"/>`;
  } else if (kind === "city") {
    shapes = `<rect y="190" width="400" height="70" fill="#2f80c8"/>
      <g fill="#35506b"><rect x="40" y="110" width="40" height="90"/><rect x="90" y="80" width="36" height="120"/>
      <rect x="136" y="125" width="44" height="75"/><rect x="190" y="60" width="34" height="140"/>
      <rect x="234" y="100" width="46" height="100"/><rect x="290" y="130" width="40" height="70"/></g>
      <g fill="#cfe8f8"><rect x="98" y="95" width="6" height="8"/><rect x="110" y="95" width="6" height="8"/>
      <rect x="198" y="75" width="6" height="8"/><rect x="210" y="75" width="6" height="8"/>
      <rect x="198" y="95" width="6" height="8"/><rect x="210" y="95" width="6" height="8"/></g>`;
  } else if (kind === "temple") {
    shapes = `<rect y="200" width="400" height="60" fill="#e9d7ab"/>
      <path d="M120 200 V130 Q200 40 280 130 V200Z" fill="#fff"/>
      <path d="M185 200 V160 Q200 140 215 160 V200Z" fill="#2f80c8"/>
      <rect x="196" y="38" width="8" height="30" fill="#fff"/>
      <rect x="85" y="150" width="28" height="50" fill="#f6efe0"/><rect x="287" y="150" width="28" height="50" fill="#f6efe0"/>`;
  } else if (kind === "pool") {
    shapes = `<path d="M0 150 Q80 90 170 140 T400 120 V260 H0Z" fill="#5fa84a"/>
      <path d="M0 190 Q120 150 240 185 T400 170 V260 H0Z" fill="#7ac143"/>
      <rect x="40" y="195" width="320" height="50" rx="10" fill="#e9f4fb"/>
      <rect x="50" y="203" width="300" height="34" rx="8" fill="#52b6e8"/>
      <path d="M60 215 Q110 207 160 215 T260 215 T340 215" stroke="#bfe8fa" stroke-width="3" fill="none"/>
      <path d="M345 190 L350 120" stroke="#6b4a2b" stroke-width="5"/>
      <path d="M350 120 Q325 105 305 120 M350 120 Q372 102 395 118" stroke="#2f7a2a" stroke-width="6" fill="none" stroke-linecap="round"/>`;
  } else { /* hero */
    shapes = `<ellipse cx="620" cy="90" rx="70" ry="22" fill="#fff" opacity=".9"/>
      <ellipse cx="680" cy="104" rx="60" ry="18" fill="#fff" opacity=".9"/>
      <ellipse cx="760" cy="200" rx="80" ry="22" fill="#fff" opacity=".8"/>
      <g transform="translate(640 230) rotate(-12)">
        <path d="M0 20 L120 0 L150 14 L120 22 L60 34 Z" fill="#fff" stroke="#c7d4e0"/>
        <path d="M60 18 L28 -26 L46 -26 L90 12Z" fill="#e9eef3" stroke="#c7d4e0"/>
        <path d="M60 30 L28 70 L46 70 L90 32Z" fill="#e9eef3" stroke="#c7d4e0"/>
        <path d="M118 6 L132 -6 L138 -6 L134 10Z" fill="#2f80c8"/>
      </g>
      <path d="M0 330 Q220 290 450 320 T900 300 V400 H0Z" fill="#4a9ad8" opacity=".85"/>
      <path d="M0 360 Q260 330 520 355 T900 340 V400 H0Z" fill="#2f80c8"/>`;
  }
  const vb = kind === "hero" ? "0 0 900 400" : "0 0 400 260";
  return `<svg viewBox="${vb}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${sky[0]}"/><stop offset="1" stop-color="${sky[1]}"/></linearGradient></defs>
    <rect width="100%" height="100%" fill="url(#${id})"/>${shapes}</svg>`;
}

document.getElementById("hero-scene").innerHTML = scene("hero");
document.querySelectorAll("[data-scene]").forEach(el => { el.innerHTML = scene(el.dataset.scene); });

/* ---------- Resort carousel ---------- */
(function () {
  const kinds = ["pool", "beach", "temple"];
  const track = document.getElementById("track");
  const dots = document.getElementById("dots");
  let index = 0;

  kinds.forEach((k, i) => {
    const s = document.createElement("div");
    s.className = "slide";
    s.innerHTML = scene(k);
    track.appendChild(s);
    const d = document.createElement("button");
    d.type = "button";
    d.className = "dot";
    d.setAttribute("aria-label", "Photo " + (i + 1));
    d.onclick = () => go(i);
    dots.appendChild(d);
  });

  function go(i) {
    index = (i + kinds.length) % kinds.length;
    track.style.transform = `translateX(-${index * 100}%)`;
    [...dots.children].forEach((d, n) => d.classList.toggle("on", n === index));
  }
  document.getElementById("prev").onclick = () => go(index - 1);
  document.getElementById("next").onclick = () => go(index + 1);
  go(0);
})();

/* ---------- Trip finder chat (talks to your Flask agent) ---------- */
const chat = document.getElementById("chat");
const approval = document.getElementById("approval");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const quick = document.getElementById("quick");

function scrollDown() { chat.scrollTop = chat.scrollHeight; }

function bubble(who, text) {
  const d = document.createElement("div");
  d.className = "bubble " + who;
  d.textContent = text;
  chat.appendChild(d);
  scrollDown();
  return d;
}

function showTyping() {
  const d = document.createElement("div");
  d.className = "bubble agent typing";
  d.innerHTML = "<i></i><i></i><i></i>";
  chat.appendChild(d);
  scrollDown();
  return d;
}

function tripFromResponse(data) {
  if (data.trip) return data.trip;
  if (!data.summary) return null;

  const fields = {};
  data.summary.split(/\r?\n/).forEach(line => {
    const separator = line.indexOf(":");
    if (separator !== -1) fields[line.slice(0, separator).trim()] = line.slice(separator + 1).trim();
  });
  const route = fields.Route && fields.Route.match(/^(.+?)\s*->\s*(.+?)\s+on\s+([^,]+),\s*(\d+)\s+night/);
  const total = fields.Total && fields.Total.match(/([\d,]+)\s+INR\s+for\s+(\d+)\s+traveler/);
  if (!route || !total || !fields.Flight || !fields.Hotel) return null;

  const budgetText = fields.Budget || "";
  const budgetMatch = budgetText.match(/(?:your budget\s+)?([\d,]+)\s+INR/);
  return {
    origin: route[1],
    destination: route[2],
    start_date: route[3],
    nights: route[4],
    flight: fields.Flight,
    hotel: fields.Hotel,
    total: total[1],
    travelers: total[2],
    budget: budgetMatch ? budgetMatch[1] : null,
    within_budget: !budgetText.includes("OVER BUDGET"),
  };
}

function addTripCard(trip) {
  const over = !trip.within_budget;
  const card = document.createElement("div");
  card.className = "trip-card" + (over ? " over" : "");
  const head = document.createElement("div");
  head.className = "head";
  head.textContent = over ? "Review: over budget" : "Review your trip";
  const details = document.createElement("dl");
  details.className = "trip-details";
  const rows = [
    ["Route", `${trip.origin} → ${trip.destination}`],
    ["Departure", trip.departure ? `${trip.start_date} · ${trip.departure}` : trip.start_date],
    ["Stay", `${trip.nights} night(s) at ${trip.hotel}`],
    ["Flight", trip.flight],
    ["Travelers", String(trip.travelers)],
    ["Estimated total", `${trip.total} INR`],
  ];
  if (trip.budget !== null) {
    rows.push(["Budget", `${trip.budget} INR${over ? " · over budget" : " · within budget"}`]);
  }
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "trip-detail";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    row.append(term, description);
    details.appendChild(row);
  });
  const actions = document.createElement("div");
  actions.className = "actions";
  const ok = document.createElement("button");
  ok.type = "button"; ok.className = "btn btn-ok"; ok.textContent = "Approve trip";
  const no = document.createElement("button");
  no.type = "button"; no.className = "btn btn-no"; no.textContent = "Reject";
  [ok, no].forEach((b, i) => {
    b.onclick = () => { ok.disabled = no.disabled = true; decide(i === 0 ? "approve" : "reject"); };
  });
  actions.append(ok, no);
  card.append(head, details, actions);
  approval.replaceChildren(card);
  approval.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function render(data) {
  bubble("agent", data.reply);
  const trip = tripFromResponse(data);
  if (data.approval && trip) addTripCard(trip);
  else if (!data.approval) approval.replaceChildren();
}

async function post(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  return r.json();
}

async function talk(url, body) {
  const t = showTyping();
  sendBtn.disabled = true;
  try { render(await post(url, body)); }
  catch (e) { bubble("agent", "Something went wrong: " + e); }
  t.remove();
  scrollDown();
  sendBtn.disabled = false;
}

function send(text) {
  text = (text || input.value).trim();
  if (!text) return;
  input.value = "";
  quick.innerHTML = "";
  bubble("user", text);
  talk("/chat", { message: text });
}

function decide(decision) { talk("/approve", { decision }); }

async function restorePendingApproval() {
  try {
    const response = await fetch("/pending-approval");
    if (response.status === 404) return;
    if (!response.ok) throw new Error("Could not check for a pending approval.");
    const data = await response.json();
    const trip = tripFromResponse(data);
    if (data.approval && trip) addTripCard(trip);
  } catch (e) {
    bubble("agent", "Could not restore pending trip approval: " + e.message);
  }
}

/* Greeting + quick replies */
bubble("agent", "Hi, I'm Johny. What are you in the mood for?");
restorePendingApproval();
["Surprise me", "Relax", "Active", "I want something relaxing"].forEach(label => {
  const c = document.createElement("button");
  c.type = "button";
  c.className = "chip";
  c.textContent = label;
  c.onclick = () => send(label);
  quick.appendChild(c);
});

sendBtn.onclick = () => send();
input.addEventListener("keydown", e => { if (e.key === "Enter") send(); });

/* Route cards prefill the trip finder */
document.querySelectorAll(".route").forEach(card => {
  card.addEventListener("click", () => {
    input.value = card.dataset.prefill;
    document.getElementById("finder").scrollIntoView({ behavior: "smooth" });
    input.focus({ preventScroll: true });
  });
});