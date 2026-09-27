# ---------- PHASE 1: DATA & REQUIREMENTS ----------

# Courses
courses = [
    {"name": "Calculus II", "credits": 4, "difficulty": "High"},
    {"name": "Intro to Psychology", "credits": 3, "difficulty": "Medium"},
    {"name": "Organic Chemistry", "credits": 4, "difficulty": "High"},
    {"name": "World History", "credits": 3, "difficulty": "Low"},
    {"name": "Spanish III", "credits": 3, "difficulty": "Medium"},
    {"name": "Intro to Statistics", "credits": 3, "difficulty": "Medium"},
]

# Deadlines
deadlines = [
    {"course": "Calculus II", "task": "Midterm Exam", "type": "Exam", "date": "2026-10-06"},
    {"course": "Calculus II", "task": "Problem Set 5", "type": "Homework", "date": "2026-09-29"},
    {"course": "Organic Chemistry", "task": "Lab Report 3", "type": "Lab", "date": "2026-10-02"},
    {"course": "Organic Chemistry", "task": "Unit Test", "type": "Exam", "date": "2026-10-10"},
    {"course": "Intro to Psychology", "task": "Essay Draft", "type": "Paper", "date": "2026-10-09"},
    {"course": "Intro to Psychology", "task": "Group Presentation", "type": "Project", "date": "2026-10-15"},
    {"course": "World History", "task": "Reading Quiz", "type": "Quiz", "date": "2026-09-30"},
    {"course": "World History", "task": "Term Paper Outline", "type": "Paper", "date": "2026-10-12"},
    {"course": "Spanish III", "task": "Oral Exam", "type": "Exam", "date": "2026-10-08"},
    {"course": "Intro to Statistics", "task": "Problem Set 4", "type": "Homework", "date": "2026-10-01"},
    {"course": "Intro to Statistics", "task": "Midterm Exam", "type": "Exam", "date": "2026-10-14"},
]

# Fixed commitments (classes, job, sleep, buffers)
fixed_commitments = [
    {"label": "Class Block", "days": ["Mon", "Wed", "Fri"], "start": "09:00", "end": "12:00"},
    {"label": "Class Block", "days": ["Tue", "Thu"], "start": "10:00", "end": "13:00"},
    {"label": "Job (Library)", "days": ["Tue", "Thu"], "start": "15:00", "end": "18:00"},
    {"label": "Job (Library)", "days": ["Sat"], "start": "09:00", "end": "13:00"},
    {"label": "Club Meeting", "days": ["Wed"], "start": "18:00", "end": "19:00"},
    {"label": "Sleep", "days": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], "start": "23:30", "end": "07:30"},
]

# Available study hours (free time windows, before hobbies/breaks are placed)
available_study_hours = [
    {"days": ["Mon", "Wed", "Fri"], "start": "13:00", "end": "15:00"},
    {"days": ["Mon", "Wed", "Fri"], "start": "19:00", "end": "21:30"},
    {"days": ["Tue", "Thu"], "start": "13:00", "end": "14:30"},
    {"days": ["Tue", "Thu"], "start": "19:00", "end": "21:30"},
    {"days": ["Sat"], "start": "14:00", "end": "17:00"},
    {"days": ["Sun"], "start": "11:00", "end": "16:00"},
]

# Hobbies / personal time to protect
hobbies = [
    {"label": "Gym", "days": ["Mon", "Wed", "Fri"], "start": "18:00", "end": "19:00"},
    {"label": "Guitar Practice", "days": ["Sun"], "start": "16:00", "end": "17:00"},
    {"label": "Call Family", "days": ["Sun"], "start": "18:00", "end": "18:30"},
    {"label": "Movie Night", "days": ["Fri"], "start": "20:00", "end": "22:00"},
    {"label": "Intramural Soccer", "days": ["Sat"], "start": "17:00", "end": "18:30"},
]

# Preferences
preferences = {
    "session_length_minutes": 50,
    "break_length_minutes": 10,
}