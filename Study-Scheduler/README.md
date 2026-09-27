# Study Scheduler

A Flask and React study-planning prototype. It builds a weekly timetable from course deadlines, available study windows, fixed commitments, hobbies, and focus/break preferences. The frontend starts with the sample semester in `mock_data.py`, so a sample timetable is generated when the app opens.


## Requirements

- Python 3.9 or newer
- Node.js 18 or newer and npm

## Setup

From the repository's `Study-Scheduler` directory, create and activate a virtual environment, then install the Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install the frontend packages:

```powershell
cd frontend
npm install
cd ..
```

## Run the App

Start the Flask API in one terminal from `Study-Scheduler`:

```powershell
python app.py
```

The API runs at `http://localhost:5000`.

Start Vite in a second terminal:

```powershell
cd Study-Scheduler\frontend
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173/`. The Flask app enables CORS for both `localhost:5173` and `127.0.0.1:5173`.

## Chat Actions

The local chat agent can update session and break lengths, add dated deadlines, rename a fixed commitment or hobby on one day, extend or shorten a commitment or hobby, convert a study block into a fixed commitment, move a named study block into an available conflict-free time, remove study blocks or commitments from a specified day, rebuild the timetable, and answer deadline questions. Duration changes keep the start time, check for overlaps, and apply only to the specified occurrence of a recurring activity. Course and activity names tolerate small spelling errors. If a request matches multiple items, the agent asks which one to change.

For example, `remove Calculus II on Tuesday` removes its Tuesday study block while keeping the course and deadline in the planner. `remove Gym on Friday` removes only Friday's occurrence while keeping Gym on its other days. `extend Guitar Practice on Sunday by 30 minutes` keeps its start time and extends its end time if the added duration does not overlap another block. `change Job on Saturday to Sleep` renames only the Saturday commitment and preserves its time. `change Spanish III on Friday to Sleep` replaces that Friday study block with a fixed Sleep block; its deadline remains in the planner. Day-specific changes persist through later timetable rebuilds.


## Prototype Limitations

Application data is held in memory and resets when the Flask process restarts. The frontend currently loads and submits the mock dataset on page load, so reloading the page replaces in-memory planner data with the sample data. Chat requests are handled by deterministic patterns rather than an external language model.
