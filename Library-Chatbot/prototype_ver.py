"""
Student Library Assistant
A single-user command-line chatbot for searching, borrowing, returning,
and tracking library books — with borrow history and due dates.
"""

import re
import difflib
from datetime import date, timedelta

LOAN_DAYS = 14
MAX_BOOKS_AT_ONCE = 3

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

open_loans = {}

history = []

for book_id, borrowed_on in open_loans.items():
    history.append({
        "book_id": book_id,
        "title": books[book_id]["title"],
        "borrowed_on": borrowed_on,
        "due_on": borrowed_on + timedelta(days=LOAN_DAYS),
        "returned_on": None,
        "status": "Borrowed",
    })

borrowed_by_user = set(open_loans.keys())

context = {"last_book": None}

BOT = "Library Assistant:"

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


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def content_tokens(text):
    return {t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1}


def is_question(message, tokens):
    return "?" in message or bool(set(tokens) & QUESTION_WORDS)


def negates_nearby(tokens, target_words, window=2):
    """Negation only counts if it's close to the relevant verb, not anywhere
    in the sentence -- so 'no I wanted to return X' doesn't misfire."""
    for i, tok in enumerate(tokens):
        if tok in target_words:
            nearby = tokens[max(0, i - window):i + window + 1]
            if set(nearby) & NEGATIONS:
                return True
    return False


def split_book_segments(message):
    """'return X and Y' -> ['return X', 'Y'] so each book resolves on its own."""
    # An author's name can also contain "and". A new segment must start with
    # a word that begins at least one title in the current catalog.
    title_starters = {tokenize(book["title"])[0] for book in books.values()}
    starters = "|".join(re.escape(word) for word in title_starters)
    separator = rf",|\band\b(?=\s+(?:{starters})\b)"
    parts = re.split(separator, message, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def choose_intent(message, tokens):
    token_set = set(tokens)

    # Small talk short-circuits everything else.
    if token_set & ACK_WORDS:
        return "acknowledge"

    found = {name for name, words in INTENTS.items() if token_set & words}

    # Typo-tolerant exit ("byee") when nothing else matched.
    if not found:
        for word in tokens:
            if difflib.get_close_matches(word, EXIT_WORDS, n=1, cutoff=0.8):
                return "exit"
        return "search"

    asking = is_question(message, tokens)
    negated = (negates_nearby(tokens, INTENTS["return"]) or
              negates_nearby(tokens, INTENTS["borrow"]))

    # "what is my borrow list" / "how many have I borrowed currently" is a
    # status check, not a checkout action.
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
    """Catches typos like 'pyhton' or 'algorithim' via edit-distance.
    Only compares against meaningful words (not stopwords like 'can'/'see'),
    and requires a tight match on words of at least 4 letters, so short
    common words can't accidentally trip a false match."""
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


def book_line(book):
    return (f'- {book["title"]} by {book["author"]} | '
            f'Shelf {book["shelf"]} | {status_of(book)}')


def book_details(book):
    return (f'{book["title"]} by {book["author"]}. Published by '
            f'{book["publisher"]} in {book["year"]}. Category: '
            f'{book["category"]}. Shelf: {book["shelf"]}. {book["pages"]} '
            f'pages. Status: {status_of(book).lower()}.')


def pretty(d):
    return d.strftime("%d %b %Y")


def ask_which(candidates, action="mean"):
    print(f"{BOT} A few books match that. Which one did you {action}?")
    for book in candidates:
        print(f'  - {book["title"]}')


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


def welcome():
    print(f"{BOT} Hello! I'm your library assistant. Here's what I can do:")
    print("  - Search by title, author, subject, or publisher")
    print("  - Check if a book is available, and find its shelf")
    print("  - Borrow and return books")
    print("  - Show your current loans, due dates, and full history")
    print("  - Recommend books by category")
    print()
    print(f"Loans last {LOAN_DAYS} days; due dates are tracked automatically.")
    print("Examples:")
    for ex in ["borrow Python Crash Course", "when is it due",
              "what have I borrowed", "recommend a programming book"]:
        print(f"  - {ex}")


def handle_help():
    print(f"{BOT} I can help with:")
    print("  - Searching by title, author, subject, or publisher")
    print("  - Checking availability and shelf location")
    print("  - Borrowing and returning books")
    print("  - Showing your current loans, due dates, and history")
    print()
    print("Examples:")
    for ex in ["borrow Python Crash Course", "when is it due",
              "what have I borrowed", "is Clean Code available?"]:
        print(f"  - {ex}")


def handle_about_bot():
    print(f"{BOT} I'm a library catalog assistant -- I look things up in "
          f"this library's records and help you borrow, return, and find "
          f"books.")


def handle_policy():
    print(f"{BOT} Loans last {LOAN_DAYS} days from the day you borrow. "
          f"You can hold up to {MAX_BOOKS_AT_ONCE} books at once. "
          f"Overdue books can still be returned any time -- I'll just note "
          f"how late it was.")


def handle_list():
    print(f"{BOT} Here is the full catalog:")
    for book in books.values():
        print(book_line(book))


def handle_category(message):
    cat = find_category(message)
    if cat is None:
        print(f"{BOT} I don't have a category matching that. Available "
              f"categories: {', '.join(sorted({b['category'] for b in books.values()}))}.")
        return
    matches = [b for b in books.values() if b["category"] == cat]
    print(f"{BOT} Books in {cat}:")
    for book in matches:
        print(book_line(book))


def handle_recommend(message):
    cat = find_category(message)
    pool = [b for b in books.values() if (cat is None or b["category"] == cat)
            and b["available"]]
    if not pool:
        print(f"{BOT} Nothing available to recommend there right now.")
        return
    pick = pool[0]
    print(f"{BOT} I'd suggest \"{pick['title']}\" by {pick['author']} "
          f"({pick['category']}, shelf {pick['shelf']}).")


def handle_details(message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(candidates)
        return
    if book is None:
        print(f"{BOT} Which book do you want details on?")
        return
    print(f"{BOT} {book_details(book)}")


def handle_my_loans():
    if not borrowed_by_user:
        print(f"{BOT} You have not borrowed anything yet.")
        return
    print(f"{BOT} You are currently holding:")
    for book_id in sorted(borrowed_by_user):
        entry = next(h for h in history
                    if h["book_id"] == book_id and h["status"] == "Borrowed")
        print(f'  - {books[book_id]["title"]} | borrowed {pretty(entry["borrowed_on"])} '
              f'| due {pretty(entry["due_on"])}')


def handle_history():
    if not history:
        print(f"{BOT} No borrow history yet.")
        return
    print(f"{BOT} Full borrow history:")
    for entry in history:
        if entry["status"] == "Returned":
            print(f'  - {entry["title"]} | borrowed {pretty(entry["borrowed_on"])} '
                  f'| returned {pretty(entry["returned_on"])}')
        else:
            flag = " (OVERDUE)" if date.today() > entry["due_on"] else ""
            print(f'  - {entry["title"]} | borrowed {pretty(entry["borrowed_on"])} '
                  f'| due {pretty(entry["due_on"])}{flag}')


def handle_overdue():
    late = [h for h in history if h["status"] == "Borrowed"
            and date.today() > h["due_on"]]
    if not late:
        print(f"{BOT} Nothing overdue. You're all clear.")
        return
    print(f"{BOT} Overdue:")
    for entry in late:
        days_late = (date.today() - entry["due_on"]).days
        print(f'  - {entry["title"]} | {days_late} day(s) overdue')


def handle_due(message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(candidates)
        return
    if book is None:
        print(f"{BOT} Which book's due date do you want?")
        return
    book_id = book_id_of(book)
    entry = next((h for h in history if h["book_id"] == book_id
                 and h["status"] == "Borrowed"), None)
    if entry is None:
        print(f'{BOT} "{book["title"]}" isn\'t currently borrowed by you.')
        return
    days_left = (entry["due_on"] - date.today()).days
    if days_left < 0:
        print(f'{BOT} "{book["title"]}" was due {pretty(entry["due_on"])} '
              f'-- {abs(days_left)} day(s) overdue.')
    else:
        print(f'{BOT} "{book["title"]}" is due {pretty(entry["due_on"])} '
              f'({days_left} day(s) left).')


def handle_borrow(message):
    for segment in split_book_segments(message):
        book, candidates = resolve_book(segment)
        if candidates:
            ask_which(candidates, "want to borrow")
            continue
        if book is None:
            print(f"{BOT} Which book would you like to borrow? Give me the "
                  f"title, author, or ISBN.")
            continue

        book_id = book_id_of(book)

        if book_id in borrowed_by_user:
            print(f'{BOT} You already have "{book["title"]}" checked out.')
            continue
        if len(borrowed_by_user) >= MAX_BOOKS_AT_ONCE:
            print(f"{BOT} You've reached the {MAX_BOOKS_AT_ONCE}-book limit. "
                  f"Return something first.")
            continue
        if not book["available"]:
            print(f'{BOT} Sorry, "{book["title"]}" is out on loan right now.')
            alts = [b for b in books.values() if b["category"] == book["category"]
                    and b["available"] and b is not book]
            if alts:
                print(f"{BOT} Similar available titles:")
                for b in alts:
                    print(book_line(b))
            continue

        book["available"] = False
        borrowed_by_user.add(book_id)
        borrowed_on = date.today()
        due_on = borrowed_on + timedelta(days=LOAN_DAYS)
        history.append({"book_id": book_id, "title": book["title"],
                        "borrowed_on": borrowed_on, "due_on": due_on,
                        "returned_on": None, "status": "Borrowed"})
        print(f'{BOT} "{book["title"]}" is checked out to you. Due back by '
              f'{pretty(due_on)}.')


def handle_return(message):
    for segment in split_book_segments(message):
        book, candidates = resolve_book(segment)
        if candidates:
            ask_which(candidates, "want to return")
            continue
        if book is None:
            print(f"{BOT} Which book would you like to return?")
            continue

        book_id = book_id_of(book)
        entry = next((h for h in history if h["book_id"] == book_id
                     and h["status"] == "Borrowed"), None)

        if entry is None:
            print(f'{BOT} "{book["title"]}" isn\'t currently borrowed by you.')
            continue

        book["available"] = True
        borrowed_by_user.discard(book_id)
        entry["returned_on"] = date.today()
        entry["status"] = "Returned"

        late_by = (entry["returned_on"] - entry["due_on"]).days
        if late_by > 0:
            print(f'{BOT} "{book["title"]}" returned -- {late_by} day(s) late. '
                  f'Please shelve it at {book["shelf"]}.')
        else:
            print(f'{BOT} "{book["title"]}" returned on time. Please shelve it '
                  f'at {book["shelf"]}.')


def handle_declined():
    print(f"{BOT} No problem, nothing borrowed.")


def handle_acknowledge():
    print(f"{BOT} You're welcome! Anything else?")


def handle_location(message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(candidates)
        return
    if book is None:
        results = find_books(message)
        if results:
            print(f"{BOT} Not sure exactly which one -- closest matches:")
            for m in results[:5]:
                print(book_line(m))
        else:
            print(f"{BOT} Which book are you looking for?")
        return
    print(f'{BOT} "{book["title"]}" is on shelf {book["shelf"]} '
          f'({book["category"]} section). {status_of(book)}.')


def handle_availability(message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(candidates)
        return
    if book is not None:
        if book["available"]:
            print(f'{BOT} Yes, "{book["title"]}" is available on shelf '
                  f'{book["shelf"]}.')
        else:
            print(f'{BOT} No, "{book["title"]}" is currently on loan.')
        return
    results = find_books(message) or list(books.values())
    available = [m for m in results if m["available"]]
    if available:
        print(f"{BOT} Available right now:")
        for m in available:
            print(book_line(m))
    else:
        print(f"{BOT} Nothing matching that is available at the moment.")


def handle_search(message):
    book, candidates = resolve_book(message)
    if candidates:
        ask_which(candidates)
        return
    if book is not None:
        print(f"{BOT} {book_details(book)}")
        return

    results = find_books(message)
    if results:
        print(f"{BOT} I found these:")
        for m in results:
            print(book_line(m))
        return

    fuzzy = suggest_close_matches(message)
    if fuzzy:
        print(f"{BOT} I couldn't find an exact answer, but did you mean:")
        for m in fuzzy:
            print(book_line(m))
        return

    print(f"{BOT} I can't answer that one -- I couldn't find anything "
          f"matching it in the catalog. I can help with book titles, "
          f"authors, subjects, availability, shelf locations, and "
          f"borrowing/returns. Try rephrasing, or type 'help' for examples.")


def chatbot():
    print(f"{BOT} Hello! How can I help you today?")

    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{BOT} Goodbye!")
            break

        if not user:
            continue

        tokens = tokenize(user)
        intent = choose_intent(user, tokens)

        if intent == "exit":
            if borrowed_by_user:
                print(f"{BOT} Reminder: you're still holding "
                      f"{len(borrowed_by_user)} book(s).")
            print(f"{BOT} Goodbye!")
            break
        elif intent == "greeting":
            print(f"{BOT} Hello! Ask me about any book, or type 'help'.")
        elif intent == "help":
            handle_help()
        elif intent == "about_bot":
            handle_about_bot()
        elif intent == "policy":
            handle_policy()
        elif intent == "list":
            handle_list()
        elif intent == "category":
            handle_category(user)
        elif intent == "recommend":
            handle_recommend(user)
        elif intent == "details":
            handle_details(user)
        elif intent == "myloans":
            handle_my_loans()
        elif intent == "history":
            handle_history()
        elif intent == "overdue":
            handle_overdue()
        elif intent == "due":
            handle_due(user)
        elif intent == "borrow":
            handle_borrow(user)
        elif intent == "return":
            handle_return(user)
        elif intent == "declined":
            handle_declined()
        elif intent == "acknowledge":
            handle_acknowledge()
        elif intent == "location":
            handle_location(user)
        elif intent == "availability":
            handle_availability(user)
        else:
            handle_search(user)


if __name__ == "__main__":
    chatbot()