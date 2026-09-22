import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import app


class PersistenceTests(unittest.TestCase):
    def test_state_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            app.STATE_FILE = Path(tmp_dir) / "library_state.json"

            app.books[1]["available"] = False
            app.history.clear()
            app.borrowed_by_user.clear()
            app.context = {"last_book": app.books[1]}

            borrowed_on = date.today()
            due_on = borrowed_on + timedelta(days=14)
            app.history.append({
                "book_id": 1,
                "title": app.books[1]["title"],
                "borrowed_on": borrowed_on,
                "due_on": due_on,
                "returned_on": None,
                "status": "Borrowed",
            })
            app.borrowed_by_user.add(1)

            app.save_state()

            app.history.clear()
            app.borrowed_by_user.clear()
            app.books[1]["available"] = True
            app.context = {"last_book": None}

            app.load_state()

            self.assertIn(1, app.borrowed_by_user)
            self.assertFalse(app.books[1]["available"])
            self.assertEqual(app.history[0]["title"], "Python Crash Course")
            self.assertEqual(app.history[0]["status"], "Borrowed")
            self.assertEqual(app.context["last_book"]["title"], "Python Crash Course")


if __name__ == "__main__":
    unittest.main()
