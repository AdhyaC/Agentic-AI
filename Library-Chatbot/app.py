"""
Student Library Assistant — Flask backend
Ports the original CLI logic to a web API. Same catalog, same intent
rules, same borrow/return/due-date behavior — just returns JSON instead
of printing to a terminal.
"""

import json
import re
import difflib
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")
STATE_FILE = Path(__file__).with_name("library_state.json")

LOAN_DAYS = 14
MAX_BOOKS_AT_ONCE = 3

# ---------------------------------------------------------------------
# Catalog & state (single-user, in-memory — same as the original script)
# ---------------------------------------------------------------------
books = {
    1: {"title": "Python Crash Course", "author": "Eric Matthes",
        "isbn": "9781593279288", "publisher": "No Starch Press", "year": 2019,
        "category": "Programming", "pages": 544, "shelf": "A-12",
        "available": True},
    2: {"title": "Clean Code", "author": "Robert C. Martin",
        "isbn": "9780132350884", "publisher": "Prentice Hall", "year": 2008,
        "category": "Programming", "pages": 464, "shelf": "A-14",
        "available": True},
    3: {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen",
        "isbn": "9780262046305", "publisher": "MIT Press", "year": 2022,
        "category": "Computer Science", "pages": 1312, "shelf": "B-05",
        "available": True},
    4: {"title": "The Pragmatic Programmer",
        "author": "David Thomas and Andrew Hunt", "isbn": "9780135957059",
        "publisher": "Addison-Wesley", "year": 2019, "category": "Programming",
        "pages": 352, "shelf": "A-16", "available": True},
    5: {"title": "Database System Concepts", "author": "Abraham Silberschatz",
        "isbn": "9780078022159", "publisher": "McGraw-Hill", "year": 2019,
        "category": "Database", "pages": 1376, "shelf": "C-03",
        "available": True},
    6: {"title": "Computer Networks", "author": "Andrew S. Tanenbaum",
        "isbn": "9780132126953", "publisher": "Pearson", "year": 2011,
        "category": "Networking", "pages": 960, "shelf": "C-10",
        "available": True},
    7: {"title": "Operating System Concepts", "author": "Abraham Silberschatz",
        "isbn": "9781119456339", "publisher": "Wiley", "year": 2018,
        "category": "Operating Systems", "pages": 976, "shelf": "B-15",
        "available": True},
    8: {"title": "Artificial Intelligence: A Modern Approach",
        "author": "Stuart Russell and Peter Norvig", "isbn": "9780134610993",
        "publisher": "Pearson", "year": 2021,
        "category": "Artificial Intelligence", "pages": 1160, "shelf": "D-02",
        "available": True},
    9: {"title": "Data Structures and Algorithms in Java",
        "author": "Robert Lafore", "isbn": "9780672324536",
        "publisher": "Sams Publishing", "year": 2002,
        "category": "Data Structures", "pages": 816, "shelf": "B-10",
        "available": True},
    10: {"title": "Engineering Mathematics", "author": "John Bird",
         "isbn": "9780415662814", "publisher": "Routledge", "year": 2017,
         "category": "Mathematics", "pages": 704, "shelf": "E-04",
         "available": True},
}

history = []                 # list of loan-record dicts
borrowed_by_user = set()     # book ids currently held
context = {"last_book": None}

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "to", "for", "and", "or", "is", "are",
    "was", "were", "do", "does", "did", "can", "could", "would", "should",
    "i", "im", "me", "my", "you", "your", "have", "has", "had", "want",
    "need", "like", "please", "book", "books", "any", "about", "with", "get",
    "give", "show", "tell", "looking", "look", "see", "now", "hello", "hi",
    "hey", "thanks", "thank", "asking", "ask", "there",
}

INTENTS = {
    "exit": {"exit", "quit", "bye", "goodbye", "close"},
    "help": {"help", "commands", "options", "guide"},
    "about_bot": {"who", "yourself", "assistant"},
    "list": {"catalog", "catalogue", "list", "everything"},
    "category": {"category", "categories", "subject", "genre", "section"},
    "recommend": {"recommend", "suggest", "suggestion"},
    "policy": {"policy", "rule", "rules", "limit", "longest"},
    "myloans": {"borrowed", "loans", "holding", "currently"},
    "history": {"history", "past", "record", "records"},
    "overdue": {"overdue", "late"},
    "due": {"due", "when", "deadline"},
    "return": {"return", "returning", "returned", "back"},
    "borrow": {"borrow", "issue", "checkout", "lend", "take", "rent"},
    "location": {"where", "shelf", "located", "location", "aisle"},
    "availability": {"available", "availability", "stock", "free"},
    "details": {"details", "info", "information", "pages", "pgs", "author",
                "wrote", "publisher", "published", "year"},
    "greeting": {"hello", "hi", "hey", "hii", "hiya", "yo"},
}

QUESTION_WORDS = {"is", "are", "do", "does", "can", "could", "what", "which",
                  "how", "when", "any", "whether", "asking", "who"}
NEGATIONS = {"no", "not", "dont", "don", "doesnt", "didnt", "never", "cant",
             "wont", "nope"}
REFERENCES = {"it", "that", "this", "one", "above", "them", "those", "same",
              "mentioned", "previous", "earlier"}
ACK_WORDS = {"thanks", "thank", "ok", "okay", "cool", "nice", "great",
             "awesome", "perfect", "sure"}
EXIT_WORDS = {"bye", "exit", "quit", "goodbye"}


# ---------------------------------------------------------------------
# Reply builder — replaces print() so handlers can send JSON back
# ---------------------------------------------------------------------
class Reply:
    def __init__(self):
        self.lines = []

    def text(self, s):
        self.lines.append({"type": "text", "text": s})

    def book_list(self, book_list):
        self.lines.append({
            "type": "books",
            "books": [
                {"title": b["title"], "author": b["author"],
                 "shelf": b["shelf"], "status": status_of(b)}
                for b in book_list
            ],
        })

    def as_json(self):
        return self.lines


# ---------------------------------------------------------------------
# NLP helpers (unchanged from the original)
# ---------------------------------------------------------------------
def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def content_tokens(text):
    return {t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1}


def is_question(message, tokens):
    return "?" in message or bool(set(tokens) & QUESTION_WORDS)


def negates_nearby(tokens, target_words, window=2):
    for i, tok in enumerate(tokens):
        if tok in target_words:
            nearby = tokens[max(0, i - window):i + window + 1]
            if set(nearby) & NEGATIONS:
                return True
    return False


def split_book_segments(message):
    title_starters = {tokenize(book["title"])[0] for book in books.values()}
    starters = "|".join(re.escape(word) for word in title_starters)
    separator = rf",|\band\b(?=\s+(?:{starters})\b)"
    parts = re.split(separator, message, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def choose_intent(message, tokens):
    token_set = set(tokens)

    if token_set & ACK_WORDS:
        return "acknowledge"

    found = {name for name, words in INTENTS.items() if token_set & words}

    if not found:
        for word in tokens:
            if difflib.get_close_matches(word, EXIT_WORDS, n=1, cutoff=0.8):
                return "exit"
        return "search"

    asking = is_question(message, tokens)
    negated = (negates_nearby(tokens, INTENTS["return"]) or
              negates_nearby(tokens, INTENTS["borrow"]))

    if "borrow" in found and ({"list", "my", "currently"} & token_set):
        found.discard("borrow")
        found.add("myloans")

    if "availability" in found and asking:
        return "availability"
    if "return" in found and (asking or negated or "due" in found):
        return "due"
    if "borrow" in found and negated:
        return "declined"

    priority = ["exit", "help", "about_bot", "policy", "overdue", "history",
                "myloans", "due", "return", "borrow", "location",
                "availability", "category", "recommend", "details", "list",
                "greeting"]
    for intent in priority:
        if intent in found:
            return intent
    return "search"


# ---------------------------------------------------------------------
# Book lookup helpers (unchanged logic)
# ---------------------------------------------------------------------
def score_book(book, message, tokens):
    lowered = message.lower()
    if book["isbn"] in re.sub(r"[^0-9]", "", lowered):
        return 1.0
    if book["title"].lower() in lowered:
        return 1.0
    title_words = content_tokens(book["title"])
    if not title_words:
        return 0.0
    return len(title_words & set(tokens)) / len(title_words)


def identify_book(message, threshold=0.5):
    tokens = tokenize(message)
    scored = []
    for book_id, book in books.items():
        score = score_book(book, message, tokens)
        if score >= threshold:
            scored.append((score, book_id, book))
    if not scored:
        return None, []
    scored.sort(key=lambda row: -row[0])
    best = scored[0][0]
    top = [row for row in scored if row[0] == best]
    if len(top) == 1:
        return top[0][2], []
    return None, [row[2] for row in top]


def fuzzy_book_guess(message):
    tokens = content_tokens(message)
    best_book, best_ratio = None, 0.0
    for book in books.values():
        for word in content_tokens(book["title"]):
            if len(word) < 4:
                continue
            match = difflib.get_close_matches(word, tokens, n=1, cutoff=0.82)
            if match:
                ratio = difflib.SequenceMatcher(None, word, match[0]).ratio()
                if ratio > best_ratio:
                    best_ratio, best_book = ratio, book
    return best_book


def resolve_book(message):
    book, candidates = identify_book(message)
    if book is not None:
        context["last_book"] = book
        return book, []
    if candidates:
        return None, candidates
    tokens = set(tokenize(message))
    if context["last_book"] and (tokens & REFERENCES):
        return context["last_book"], []
    guess = fuzzy_book_guess(message)
    if guess:
        context["last_book"] = guess
        return guess, []
    return None, []


def find_books(message):
    tokens = content_tokens(message)
    if not tokens:
        return []
    results = []
    for book in books.values():
        haystack = content_tokens(
            f'{book["title"]} {book["author"]} {book["category"]} '
            f'{book["publisher"]}')
        hits = len(tokens & haystack)
        if hits:
            results.append((hits, book))
    results.sort(key=lambda row: -row[0])
    return [book for _, book in results]


def find_category(message):
    tokens = content_tokens(message)
    for book in books.values():
        if tokens & content_tokens(book["category"]):
            return book["category"]
    all_cats = {b["category"] for b in books.values()}
    for cat in all_cats:
        if difflib.get_close_matches(cat.lower(), list(tokens), cutoff=0.6):
            return cat
    return None


def book_id_of(target):
    for book_id, book in books.items():
        if book is target:
            return book_id
    return None


def status_of(book):
    return "Available" if book["available"] else "Currently borrowed"


def book_details(book):
    return (f'{book["title"]} by {book["author"]}. Published by '
            f'{book["publisher"]} in {book["year"]}. Category: '
            f'{book["category"]}. Shelf: {book["shelf"]}. {book["pages"]} '
            f'pages. Status: {status_of(book).lower()}.')


def pretty(d):
    return d.strftime("%d %b %Y")


def suggest_close_matches(message):
    tokens = content_tokens(message)
    all_words = set()
    for book in books.values():
        all_words |= content_tokens(book["title"])
        all_words |= content_tokens(book["author"])
    hits = set()
    for word in tokens:
        hits |= set(difflib.get_close_matches(word, all_words, n=2, cutoff=0.7))
    if not hits:
        return []
    results = []
    for book in books.values():
        pool = content_tokens(book["title"]) | content_tokens(book["author"])
        if pool & hits:
            results.append(book)
    return results


# ---------------------------------------------------------------------
# Intent handlers — same behavior as the CLI, writing into `reply`
# instead of printing
# ---------------------------------------------------------------------
def ask_which(reply, candidates, action="mean"):
    reply.text(f"A few books match that. Which one did you {action}?")
    reply.book_list(candidates)


def handle_help(reply):
    reply.text("I can help with:\n- Searching by title, author, subject, or publisher\n"
                "- Checking availability and shelf location\n"
                "- Borrowing and returning books\n"
                "- Showing your current loans, due dates, and history\n\n"
                "Try: 'borrow Python Crash Course', 'when is it due', "
                "'what have I borrowed'")


def handle_about_bot(reply):
    reply.text("I'm a library catalog assistant — I look things up in this "
               "library's records and help you borrow, return, and find books.")


def handle_policy(reply):
    reply.text(f"Loans last {LOAN_DAYS} days from the day you borrow. "
               f"You can hold up to {MAX_BOOKS_AT_ONCE} books at once. "
               f"Overdue books can still be returned any time — I'll just "
               f"note how late it was.")


def handle_list(reply):
    reply.text("Here is the full catalog:")
    reply.book_list(list(books.values()))


def handle_category(reply, message):
    cat = find_category(message)
    if cat is None:
        cats = ", ".join(sorted({b["category"] for b in books.values()}))
        reply.text(f"I don't have a category matching that. Available "
                   f"categories: {cats}.")
        return
    matches = [b for b in books.values() if b["category"] == cat]
    reply.text(f"Books in {cat}:")
    reply.book_list(matches)


def handle_recommend(reply, message):
    cat = find_category(message)
    pool = [b for b in books.values() if (cat is None or b["category"] == cat)
            and b["available"]]
    if not pool:
        reply.text("Nothing available to recommend there right now.")
        return
    pick = pool[0]
    reply.text(f'I\'d suggest "{pick["title"]}" by {pick["author"]} '
              f'({pick["category"]}, shelf {pick["shelf"]}).')


def handle_details(reply, message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(reply, candidates)
        return
    if book is None:
        reply.text("Which book do you want details on?")
        return
    reply.text(book_details(book))


def handle_my_loans(reply):
    if not borrowed_by_user:
        reply.text("You have not borrowed anything yet.")
        return
    reply.text("You are currently holding:")
    lines = []
    for book_id in sorted(borrowed_by_user):
        entry = next(h for h in history
                    if h["book_id"] == book_id and h["status"] == "Borrowed")
        lines.append(f'{books[book_id]["title"]} — borrowed '
                     f'{pretty(entry["borrowed_on"])} · due '
                     f'{pretty(entry["due_on"])}')
    reply.lines.append({"type": "text", "text": "\n".join(lines)})


def handle_history(reply):
    if not history:
        reply.text("No borrow history yet.")
        return
    reply.text("Full borrow history:")
    lines = []
    for entry in history:
        if entry["status"] == "Returned":
            lines.append(f'{entry["title"]} — borrowed '
                         f'{pretty(entry["borrowed_on"])} · returned '
                         f'{pretty(entry["returned_on"])}')
        else:
            flag = " (OVERDUE)" if date.today() > entry["due_on"] else ""
            lines.append(f'{entry["title"]} — borrowed '
                         f'{pretty(entry["borrowed_on"])} · due '
                         f'{pretty(entry["due_on"])}{flag}')
    reply.lines.append({"type": "text", "text": "\n".join(lines)})


def handle_overdue(reply):
    late = [h for h in history if h["status"] == "Borrowed"
            and date.today() > h["due_on"]]
    if not late:
        reply.text("Nothing overdue. You're all clear.")
        return
    reply.text("Overdue:")
    lines = [f'{e["title"]} — {(date.today() - e["due_on"]).days} day(s) overdue'
             for e in late]
    reply.lines.append({"type": "text", "text": "\n".join(lines)})


def handle_due(reply, message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(reply, candidates)
        return
    if book is None:
        reply.text("Which book's due date do you want?")
        return
    book_id = book_id_of(book)
    entry = next((h for h in history if h["book_id"] == book_id
                 and h["status"] == "Borrowed"), None)
    if entry is None:
        reply.text(f'"{book["title"]}" isn\'t currently borrowed by you.')
        return
    days_left = (entry["due_on"] - date.today()).days
    if days_left < 0:
        reply.text(f'"{book["title"]}" was due {pretty(entry["due_on"])} — '
                   f'{abs(days_left)} day(s) overdue.')
    else:
        reply.text(f'"{book["title"]}" is due {pretty(entry["due_on"])} '
                   f'({days_left} day(s) left).')


def handle_borrow(reply, message):
    for segment in split_book_segments(message):
        book, candidates = resolve_book(segment)
        if candidates:
            ask_which(reply, candidates, "want to borrow")
            continue
        if book is None:
            reply.text("Which book would you like to borrow? Give me the "
                       "title, author, or ISBN.")
            continue

        book_id = book_id_of(book)

        if book_id in borrowed_by_user:
            reply.text(f'You already have "{book["title"]}" checked out.')
            continue
        if len(borrowed_by_user) >= MAX_BOOKS_AT_ONCE:
            reply.text(f"You've reached the {MAX_BOOKS_AT_ONCE}-book limit. "
                      f"Return something first.")
            continue
        if not book["available"]:
            reply.text(f'Sorry, "{book["title"]}" is out on loan right now.')
            alts = [b for b in books.values() if b["category"] == book["category"]
                    and b["available"] and b is not book]
            if alts:
                reply.text("Similar available titles:")
                reply.book_list(alts)
            continue

        book["available"] = False
        borrowed_by_user.add(book_id)
        borrowed_on = date.today()
        due_on = borrowed_on + timedelta(days=LOAN_DAYS)
        history.append({"book_id": book_id, "title": book["title"],
                        "borrowed_on": borrowed_on, "due_on": due_on,
                        "returned_on": None, "status": "Borrowed"})
        reply.text(f'"{book["title"]}" is checked out to you. Due back by '
                  f'{pretty(due_on)}.')


def handle_return(reply, message):
    for segment in split_book_segments(message):
        book, candidates = resolve_book(segment)
        if candidates:
            ask_which(reply, candidates, "want to return")
            continue
        if book is None:
            reply.text("Which book would you like to return?")
            continue

        book_id = book_id_of(book)
        entry = next((h for h in history if h["book_id"] == book_id
                     and h["status"] == "Borrowed"), None)

        if entry is None:
            reply.text(f'"{book["title"]}" isn\'t currently borrowed by you.')
            continue

        book["available"] = True
        borrowed_by_user.discard(book_id)
        entry["returned_on"] = date.today()
        entry["status"] = "Returned"

        late_by = (entry["returned_on"] - entry["due_on"]).days
        if late_by > 0:
            reply.text(f'"{book["title"]}" returned — {late_by} day(s) late. '
                      f'Please shelve it at {book["shelf"]}.')
        else:
            reply.text(f'"{book["title"]}" returned on time. Please shelve '
                      f'it at {book["shelf"]}.')


def handle_location(reply, message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(reply, candidates)
        return
    if book is None:
        results = find_books(message)
        if results:
            reply.text("Not sure exactly which one — closest matches:")
            reply.book_list(results[:5])
        else:
            reply.text("Which book are you looking for?")
        return
    reply.text(f'"{book["title"]}" is on shelf {book["shelf"]} '
              f'({book["category"]} section). {status_of(book)}.')


def handle_availability(reply, message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(reply, candidates)
        return
    if book is not None:
        if book["available"]:
            reply.text(f'Yes, "{book["title"]}" is available on shelf '
                      f'{book["shelf"]}.')
        else:
            reply.text(f'No, "{book["title"]}" is currently on loan.')
        return
    results = find_books(message) or list(books.values())
    available = [m for m in results if m["available"]]
    if available:
        reply.text("Available right now:")
        reply.book_list(available)
    else:
        reply.text("Nothing matching that is available at the moment.")


def handle_search(reply, message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(reply, candidates)
        return
    if book is not None:
        reply.text(book_details(book))
        return

    results = find_books(message)
    if results:
        reply.text("I found these:")
        reply.book_list(results)
        return

    fuzzy = suggest_close_matches(message)
    if fuzzy:
        reply.text("I couldn't find an exact answer, but did you mean:")
        reply.book_list(fuzzy)
        return

    reply.text("I can't answer that one — I couldn't find anything matching "
              "it in the catalog. I can help with book titles, authors, "
              "subjects, availability, shelf locations, and "
              "borrowing/returns. Try rephrasing, or type 'help' for "
              "examples.")


# ---------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------
def route_message(reply, message):
    tokens = tokenize(message)
    intent = choose_intent(message, tokens)

    if intent == "exit":
        if borrowed_by_user:
            reply.text(f"Reminder: you're still holding "
                      f"{len(borrowed_by_user)} book(s).")
        reply.text("Goodbye!")
    elif intent == "greeting":
        reply.text("Hello! Ask me about any book, or type 'help'.")
    elif intent == "help":
        handle_help(reply)
    elif intent == "about_bot":
        handle_about_bot(reply)
    elif intent == "policy":
        handle_policy(reply)
    elif intent == "list":
        handle_list(reply)
    elif intent == "category":
        handle_category(reply, message)
    elif intent == "recommend":
        handle_recommend(reply, message)
    elif intent == "details":
        handle_details(reply, message)
    elif intent == "myloans":
        handle_my_loans(reply)
    elif intent == "history":
        handle_history(reply)
    elif intent == "overdue":
        handle_overdue(reply)
    elif intent == "due":
        handle_due(reply, message)
    elif intent == "borrow":
        handle_borrow(reply, message)
    elif intent == "return":
        handle_return(reply, message)
    elif intent == "declined":
        reply.text("No problem, nothing borrowed.")
    elif intent == "acknowledge":
        reply.text("You're welcome! Anything else?")
    elif intent == "location":
        handle_location(reply, message)
    elif intent == "availability":
        handle_availability(reply, message)
    else:
        handle_search(reply, message)


def current_loans():
    """Serialized loan list for the sidebar."""
    today = date.today()
    out = []
    for book_id in sorted(borrowed_by_user):
        entry = next(h for h in history
                    if h["book_id"] == book_id and h["status"] == "Borrowed")
        days_left = (entry["due_on"] - today).days
        out.append({
            "title": books[book_id]["title"],
            "borrowedOn": pretty(entry["borrowed_on"]),
            "dueOn": pretty(entry["due_on"]),
            "daysLeft": days_left,
        })
    return out


def save_state():
    """Persist the current library state so it survives restarts."""
    payload = {
        "books": {
            str(book_id): {
                "title": book["title"],
                "author": book["author"],
                "isbn": book["isbn"],
                "publisher": book["publisher"],
                "year": book["year"],
                "category": book["category"],
                "pages": book["pages"],
                "shelf": book["shelf"],
                "available": bool(book["available"]),
            }
            for book_id, book in books.items()
        },
        "borrowed_by_user": sorted(borrowed_by_user),
        "history": [
            {
                "book_id": entry["book_id"],
                "title": entry["title"],
                "borrowed_on": entry["borrowed_on"].isoformat() if isinstance(entry.get("borrowed_on"), date) else entry.get("borrowed_on"),
                "due_on": entry["due_on"].isoformat() if isinstance(entry.get("due_on"), date) else entry.get("due_on"),
                "returned_on": entry["returned_on"].isoformat() if isinstance(entry.get("returned_on"), date) else entry.get("returned_on"),
                "status": entry.get("status", "Borrowed"),
            }
            for entry in history
        ],
        "context": {
            "last_book": book_id_of(context.get("last_book")) if context.get("last_book") else None,
        },
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state():
    """Restore the saved library state when the app starts."""
    if not STATE_FILE.exists():
        return

    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    if not isinstance(payload, dict):
        return

    for book_id, item in payload.get("books", {}).items():
        try:
            book_key = int(book_id)
        except (TypeError, ValueError):
            continue
        if book_key not in books:
            continue
        for key, value in item.items():
            if key in {"year", "pages"}:
                books[book_key][key] = int(value)
            elif key == "available":
                books[book_key][key] = bool(value)
            else:
                books[book_key][key] = value

    borrowed_by_user.clear()
    for book_id in payload.get("borrowed_by_user", []):
        try:
            borrowed_by_user.add(int(book_id))
        except (TypeError, ValueError):
            continue

    history.clear()
    for entry in payload.get("history", []):
        record = {
            "book_id": int(entry.get("book_id", 0)),
            "title": entry.get("title", ""),
            "borrowed_on": date.fromisoformat(entry["borrowed_on"]) if entry.get("borrowed_on") else None,
            "due_on": date.fromisoformat(entry["due_on"]) if entry.get("due_on") else None,
            "returned_on": date.fromisoformat(entry["returned_on"]) if entry.get("returned_on") else None,
            "status": entry.get("status", "Borrowed"),
        }
        history.append(record)

    last_book_id = payload.get("context", {}).get("last_book")
    context["last_book"] = books.get(int(last_book_id)) if last_book_id is not None else None


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()

    reply = Reply()
    if message:
        route_message(reply, message)
        save_state()

    return jsonify({
        "lines": reply.as_json(),
        "loans": current_loans(),
    })


load_state()


if __name__ == "__main__":
    app.run(debug=True, port=5000)