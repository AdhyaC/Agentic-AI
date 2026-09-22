/* =========================================================
   Thin client — no library/intent logic here.
   Every message is sent to the Flask backend (`/chat`), which
   runs the actual library_assistant.py logic and returns:
     { lines: [ {type:"text", text}, {type:"books", books:[...]} ],
       loans: [ {title, borrowedOn, dueOn, daysLeft} ] }
   This file only sends requests and renders the response.
   ========================================================= */

const chatWindow = document.getElementById("chatWindow");
const loansList = document.getElementById("loansList");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const quickReplies = document.getElementById("quickReplies");

/* ---------- Rendering helpers ---------- */
function addMessage(text, sender = "bot") {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addBookList(bookArray) {
  const div = document.createElement("div");
  div.className = "msg bot";
  bookArray.forEach(book => {
    const line = document.createElement("span");
    line.className = "book-line";
    line.textContent = `${book.title} — ${book.author ?? ""} · Shelf ${book.shelf} · ${book.status}`;
    div.appendChild(line);
  });
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function renderReplyLines(lines) {
  lines.forEach(line => {
    if (line.type === "text") addMessage(line.text, "bot");
    else if (line.type === "books") addBookList(line.books);
  });
}

function renderLoans(loans) {
  loansList.innerHTML = "";
  if (!loans || loans.length === 0) {
    loansList.innerHTML = `<p class="empty-state">Nothing checked out yet — borrow a book and it'll show up here.</p>`;
    return;
  }
  loans.forEach(loan => {
    let badgeClass = "ok", badgeText = `${loan.daysLeft}d left`;
    if (loan.daysLeft < 0) { badgeClass = "overdue"; badgeText = `${Math.abs(loan.daysLeft)}d overdue`; }
    else if (loan.daysLeft <= 3) { badgeClass = "soon"; badgeText = `${loan.daysLeft}d left`; }

    const card = document.createElement("div");
    card.className = "loan-card";
    card.innerHTML = `
      <p class="loan-title">${loan.title}</p>
      <div class="loan-due">
        Due ${loan.dueOn}
        <span class="due-badge ${badgeClass}">${badgeText}</span>
      </div>`;
    loansList.appendChild(card);
  });
}

/* ---------- Talk to the Flask backend ---------- */
async function sendMessage(text) {
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const data = await res.json();
    renderReplyLines(data.lines);
    renderLoans(data.loans);
  } catch (err) {
    addMessage("Something went wrong reaching the library server. Is app.py running?", "bot");
    console.error(err);
  }
}

/* ---------- Wire up UI ---------- */
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  addMessage(text, "user");
  chatInput.value = "";
  sendMessage(text);
});

quickReplies.addEventListener("click", (e) => {
  if (!e.target.classList.contains("chip")) return;
  const text = e.target.textContent;
  addMessage(text, "user");
  sendMessage(text);
});

/* ---------- Boot ---------- */
addMessage("Hello! I'm your library assistant. Ask me about a book, or tap an example below to get started.");
renderLoans([]);