import React, { useEffect, useState } from "react";
import {
  fetchMockData,
  generateSchedule,
  sendCoachMessage,
  submitIntake,
} from "./api";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_NAMES = {
  Mon: "Monday",
  Tue: "Tuesday",
  Wed: "Wednesday",
  Thu: "Thursday",
  Fri: "Friday",
  Sat: "Saturday",
  Sun: "Sunday",
};
const DEADLINE_TYPES = ["Exam", "Project", "Paper", "Lab", "Quiz", "Homework"];
const EMPTY_INTAKE = {
  courses: [{ name: "", credits: 3, difficulty: "Medium" }],
  deadlines: [{ course: "", task: "", type: "Exam", date: "" }],
  fixed_commitments: [],
  available_study_hours: [{ days: ["Mon"], start: "13:00", end: "17:00" }],
  hobbies: [],
  preferences: { session_length_minutes: 50, break_length_minutes: 10 },
};

function Field({ label, className = "", ...props }) {
  return (
    <label className={`field ${className}`}>
      <span>{label}</span>
      <input {...props} />
    </label>
  );
}

function SelectField({ label, options, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select {...props}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}

function DaysField({ value, onChange }) {
  const toggleDay = (day) => {
    onChange(value.includes(day)
      ? value.filter((selected) => selected !== day)
      : DAYS.filter((candidate) => value.includes(candidate) || candidate === day));
  };

  return (
    <fieldset className="days-field">
      <legend>Days</legend>
      <div className="day-options">
        {DAYS.map((day) => (
          <label className="day-option" key={day}>
            <input
              type="checkbox"
              checked={value.includes(day)}
              onChange={() => toggleDay(day)}
            />
            <span>{day}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function ListSection({ title, description, items, addLabel, onAdd, onRemove, children }) {
  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <button className="text-button" type="button" onClick={onAdd}>+ {addLabel}</button>
      </div>
      <div className="entry-list">
        {items.length === 0 && <p className="empty-note">Nothing added yet.</p>}
        {items.map((item, index) => (
          <div className="entry-row" key={`${title}-${index}`}>
            <div className="entry-fields">{children(item, index)}</div>
            <button
              className="remove-button"
              type="button"
              onClick={() => onRemove(index)}
              aria-label={`Remove ${title.toLowerCase()} ${index + 1}`}
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

function WeekView({ table, isMockTimetable }) {
  const allItems = DAYS.flatMap((day) => table[day] || []);
  const studyItems = allItems.filter((item) => item.category === "Study");
  const studyMinutes = studyItems.reduce((total, item) => {
    const [startHour, startMinute] = item.start.split(":").map(Number);
    const [endHour, endMinute] = item.end.split(":").map(Number);
    return total + (endHour * 60 + endMinute) - (startHour * 60 + startMinute);
  }, 0);

  return (
    <>
      <div className="week-summary">
        <div>
          <p className="eyebrow">{isMockTimetable ? "Sample plan · generated from mock data" : "Your generated plan"}</p>
          <h2>A week with room to focus.</h2>
        </div>
        <div className="summary-stats">
          <div><strong>{studyItems.length}</strong><span>study sessions</span></div>
          <div><strong>{(studyMinutes / 60).toFixed(1)}</strong><span>study hours</span></div>
          <div><strong>{allItems.length}</strong><span>planned blocks</span></div>
        </div>
      </div>

      {studyItems.length === 0 && (
        <div className="notice">
          No study sessions were placed. Add upcoming deadlines and available study hours, then generate again.
        </div>
      )}

      <div className="week-scroll" aria-label="Weekly timetable">
        <div className="week-grid">
          {DAYS.map((day) => {
            const items = table[day] || [];
            return (
              <section className="day-column" key={day}>
                <header className="day-heading">
                  <span>{DAY_NAMES[day]}</span>
                  <span className="day-count">{items.length}</span>
                </header>
                <div className="day-events">
                  {items.length === 0 && <p className="day-empty">Open day</p>}
                  {items.map((item, index) => (
                    <article className={`event event-${item.category.toLowerCase()}`} key={`${item.start}-${index}`}>
                      <span className="event-time">{item.start}–{item.end}</span>
                      <strong>{item.label}</strong>
                      <span className="event-category">{item.category}</span>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </div>
      <div className="legend" aria-label="Schedule categories">
        {["Study", "Fixed", "Hobby"].map((category) => (
          <span key={category}><i className={`legend-dot legend-${category.toLowerCase()}`} />{category}</span>
        ))}
      </div>
    </>
  );
}

function CoachPanel({ messages, onSend, isSending }) {
  const [input, setInput] = useState("");
  const handleSubmit = (event) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) return;
    onSend(message);
    setInput("");
  };

  return (
    <section className="coach-section">
      <div>
        <p className="eyebrow">A quick check-in</p>
        <h2>Tell me what you need.</h2>
        <p className="coach-hint">Ask me to move, extend, shorten, rename, or remove a scheduled activity. I check changes against the rest of your day.</p>
      </div>
      <div className="coach-thread" aria-live="polite">
        {messages.map((message, index) => (
          <p className={`coach-message coach-${message.role}`} key={index}>{message.text}</p>
        ))}
        {isSending && <p className="coach-message coach-working">Updating your timetable…</p>}
      </div>
      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          className="input-bar"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about your study plan"
          aria-label="Message the study coach"
        />
        <button className="button button-dark" type="submit" disabled={!input.trim() || isSending}>
          {isSending ? "Working…" : "Send"}
        </button>
      </form>
    </section>
  );
}

export default function App() {
  const [form, setForm] = useState(EMPTY_INTAKE);
  const [table, setTable] = useState(null);
  const [activeView, setActiveView] = useState("week");
  const [isLoadingDemo, setIsLoadingDemo] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAgentWorking, setIsAgentWorking] = useState(false);
  const [isMockTimetable, setIsMockTimetable] = useState(true);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Your sample week is ready. Try ‘extend Guitar Practice on Sunday by 30 minutes’, ‘shorten Gym on Friday by 15 minutes’, or ‘move Calculus II Midterm to Tuesday at 20:00’. If a request matches several blocks, I’ll ask which one." },
  ]);

  useEffect(() => {
    let active = true;

    const loadMockTimetable = async () => {
      try {
        const mockResponse = await fetchMockData();
        if (mockResponse.status !== "ok") {
          throw new Error("The sample planner data could not be loaded.");
        }

        const intake = mockResponse.intake;
        if (active) setForm(intake);

        const intakeResponse = await submitIntake(intake);
        if (intakeResponse.status !== "ok") {
          throw new Error("The sample planner data could not be saved.");
        }

        const scheduleResponse = await generateSchedule();
        if (scheduleResponse.status !== "ok") {
          throw new Error(scheduleResponse.message || "The sample timetable could not be generated.");
        }
        if (active) setTable(scheduleResponse.weekly_table);
      } catch (loadError) {
        if (active) {
          setError(loadError.message || "Could not connect to the scheduler backend.");
          setActiveView("intake");
        }
      } finally {
        if (active) setIsLoadingDemo(false);
      }
    };

    loadMockTimetable();
    return () => { active = false; };
  }, []);

  const updateEntry = (section, index, key, value) => {
    setIsMockTimetable(false);
    setForm((current) => ({
      ...current,
      [section]: current[section].map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, [key]: value } : entry),
    }));
  };

  const addEntry = (section, entry) => {
    setIsMockTimetable(false);
    setForm((current) => ({ ...current, [section]: [...current[section], entry] }));
  };

  const removeEntry = (section, index) => {
    setIsMockTimetable(false);
    setForm((current) => ({
      ...current,
      [section]: current[section].filter((_, entryIndex) => entryIndex !== index),
    }));
  };

  const updatePreference = (key, value) => {
    setIsMockTimetable(false);
    setForm((current) => ({
      ...current,
      preferences: { ...current.preferences, [key]: Number(value) },
    }));
  };

  const generateFromCurrentIntake = async () => {
    setError("");
    setIsGenerating(true);
    try {
      const intakeResponse = await submitIntake(form);
      if (intakeResponse.status !== "ok") {
        throw new Error((intakeResponse.errors || [intakeResponse.message || "Check your details and try again."]).join(" "));
      }
      const scheduleResponse = await generateSchedule();
      if (scheduleResponse.status !== "ok") {
        throw new Error(scheduleResponse.message || "The timetable could not be generated.");
      }
      setTable(scheduleResponse.weekly_table);
      setIsMockTimetable(false);
      setActiveView("week");
    } catch (generationError) {
      setError(generationError.message || "Could not reach the scheduler. Check that the backend is running.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerate = (event) => {
    event.preventDefault();
    return generateFromCurrentIntake();
  };

  const handleCoachSend = async (text) => {
    setMessages((current) => [...current, { role: "user", text }]);
    setIsAgentWorking(true);
    try {
      const response = await sendCoachMessage(text);
      if (response.weekly_table) {
        setTable(response.weekly_table);
        setIsMockTimetable(false);
      }
      if (response.intake) setForm(response.intake);
      setMessages((current) => [...current, {
        role: "assistant",
        text: response.reply || response.message || "I couldn't process that message.",
      }]);
    } catch {
      setMessages((current) => [...current, {
        role: "assistant",
        text: "I couldn't connect to the scheduler. Check that the backend is running and try again.",
      }]);
    } finally {
      setIsAgentWorking(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Study Scheduler home">
          <span className="brand-mark">S</span>
          <span>Study Scheduler</span>
        </a>
        <span className="header-note">A calmer way to plan your week</span>
      </header>

      <main id="top" className="page-content">
        <section className="intro">
          <div>
            <p className="eyebrow">Your semester, in rhythm</p>
            <h1>Make a week that<br />makes room for you.</h1>
            <p className="intro-copy">Add your deadlines and real-life commitments. Your study sessions will find the gaps.</p>
          </div>
          <div className="step-indicator" aria-label={`Step ${activeView === "intake" ? 1 : 2} of 2`}>
            <span className={activeView === "intake" ? "step-active" : "step-done"}>01 <i>Details</i></span>
            <span className="step-rule" />
            <span className={activeView === "week" ? "step-active" : ""}>02 <i>Your week</i></span>
          </div>
        </section>

        <nav className="view-tabs" aria-label="Planner views">
          <button
            className={activeView === "intake" ? "view-tab selected" : "view-tab"}
            type="button"
            onClick={() => setActiveView("intake")}
            disabled={isLoadingDemo}
          >
            01 <span>Planner details</span>
          </button>
          <button
            className={activeView === "week" ? "view-tab selected" : "view-tab"}
            type="button"
            onClick={() => table && setActiveView("week")}
            disabled={!table || isLoadingDemo}
          >
            02 <span>Weekly timetable</span>
          </button>
        </nav>

        {activeView === "intake" ? (
          <form className="planner-form" onSubmit={handleGenerate}>
            <ListSection
              title="Your courses"
              description="What are you studying this term?"
              items={form.courses}
              addLabel="Add course"
              onAdd={() => addEntry("courses", { name: "", credits: 3, difficulty: "Medium" })}
              onRemove={(index) => removeEntry("courses", index)}
            >
              {(course, index) => (
                <>
                  <Field label="Course name" value={course.name} onChange={(event) => updateEntry("courses", index, "name", event.target.value)} placeholder="e.g. Biology 201" required />
                  <Field label="Credits" type="number" min="1" max="30" value={course.credits} onChange={(event) => updateEntry("courses", index, "credits", Number(event.target.value))} required />
                  <SelectField label="Difficulty" value={course.difficulty} onChange={(event) => updateEntry("courses", index, "difficulty", event.target.value)} options={["Low", "Medium", "High"].map((value) => ({ value, label: value }))} />
                </>
              )}
            </ListSection>

            <ListSection
              title="Upcoming deadlines"
              description="Closer, higher-stakes work gets scheduled first."
              items={form.deadlines}
              addLabel="Add deadline"
              onAdd={() => addEntry("deadlines", { course: "", task: "", type: "Exam", date: "" })}
              onRemove={(index) => removeEntry("deadlines", index)}
            >
              {(deadline, index) => (
                <>
                  <Field label="Course" value={deadline.course} onChange={(event) => updateEntry("deadlines", index, "course", event.target.value)} placeholder="Course name" required />
                  <Field label="Task" value={deadline.task} onChange={(event) => updateEntry("deadlines", index, "task", event.target.value)} placeholder="e.g. Midterm" required />
                  <SelectField label="Type" value={deadline.type} onChange={(event) => updateEntry("deadlines", index, "type", event.target.value)} options={DEADLINE_TYPES.map((value) => ({ value, label: value }))} />
                  <Field label="Due date" type="date" value={deadline.date} onChange={(event) => updateEntry("deadlines", index, "date", event.target.value)} required />
                </>
              )}
            </ListSection>

            <ListSection
              title="Available study time"
              description="Windows when you can focus."
              items={form.available_study_hours}
              addLabel="Add time window"
              onAdd={() => addEntry("available_study_hours", { days: [], start: "09:00", end: "12:00" })}
              onRemove={(index) => removeEntry("available_study_hours", index)}
            >
              {(window, index) => (
                <>
                  <DaysField value={window.days} onChange={(days) => updateEntry("available_study_hours", index, "days", days)} />
                  <Field label="From" type="time" value={window.start} onChange={(event) => updateEntry("available_study_hours", index, "start", event.target.value)} required />
                  <Field label="To" type="time" value={window.end} onChange={(event) => updateEntry("available_study_hours", index, "end", event.target.value)} required />
                </>
              )}
            </ListSection>

            <ListSection
              title="Fixed commitments"
              description="Classes, work, or other time that is already spoken for."
              items={form.fixed_commitments}
              addLabel="Add commitment"
              onAdd={() => addEntry("fixed_commitments", { label: "", days: [], start: "09:00", end: "10:00" })}
              onRemove={(index) => removeEntry("fixed_commitments", index)}
            >
              {(commitment, index) => (
                <>
                  <Field label="What" value={commitment.label} onChange={(event) => updateEntry("fixed_commitments", index, "label", event.target.value)} placeholder="e.g. Lecture" required />
                  <DaysField value={commitment.days} onChange={(days) => updateEntry("fixed_commitments", index, "days", days)} />
                  <Field label="From" type="time" value={commitment.start} onChange={(event) => updateEntry("fixed_commitments", index, "start", event.target.value)} required />
                  <Field label="To" type="time" value={commitment.end} onChange={(event) => updateEntry("fixed_commitments", index, "end", event.target.value)} required />
                </>
              )}
            </ListSection>

            <ListSection
              title="Life outside class"
              description="Keep hobbies and personal time in your week, too."
              items={form.hobbies}
              addLabel="Add activity"
              onAdd={() => addEntry("hobbies", { label: "", days: [], start: "18:00", end: "19:00" })}
              onRemove={(index) => removeEntry("hobbies", index)}
            >
              {(hobby, index) => (
                <>
                  <Field label="Activity" value={hobby.label} onChange={(event) => updateEntry("hobbies", index, "label", event.target.value)} placeholder="e.g. Gym" required />
                  <DaysField value={hobby.days} onChange={(days) => updateEntry("hobbies", index, "days", days)} />
                  <Field label="From" type="time" value={hobby.start} onChange={(event) => updateEntry("hobbies", index, "start", event.target.value)} required />
                  <Field label="To" type="time" value={hobby.end} onChange={(event) => updateEntry("hobbies", index, "end", event.target.value)} required />
                </>
              )}
            </ListSection>

            <section className="form-section preferences-section">
              <div className="section-heading">
                <div><h2>Study preferences</h2><p>Choose a pace that works for you.</p></div>
              </div>
              <div className="preference-fields">
                <Field label="Focus session (minutes)" type="number" min="15" max="180" step="5" value={form.preferences.session_length_minutes} onChange={(event) => updatePreference("session_length_minutes", event.target.value)} required />
                <Field label="Break between sessions (minutes)" type="number" min="0" max="60" step="5" value={form.preferences.break_length_minutes} onChange={(event) => updatePreference("break_length_minutes", event.target.value)} required />
              </div>
            </section>

            {error && <div className="form-error" role="alert">{error}</div>}
            <div className="form-actions">
              <p>Upcoming deadlines guide how study time is prioritized.</p>
              <button className="button button-dark generate-button" type="submit" disabled={isGenerating}>
                {isGenerating ? "Building your week…" : "Build my timetable"}
                {!isGenerating && <span aria-hidden="true">↗</span>}
              </button>
            </div>
          </form>
        ) : (
          <div className="week-view">
            {isLoadingDemo ? (
              <div className="loading-state" role="status">Building a sample week from your course and deadline data…</div>
            ) : table ? (
              <>
                <div className="week-actions">
                  <button className="text-button" type="button" onClick={() => setActiveView("intake")}>← Edit planner details</button>
                </div>
                <CoachPanel messages={messages} onSend={handleCoachSend} isSending={isAgentWorking} />
                <WeekView table={table} isMockTimetable={isMockTimetable} />
              </>
            ) : (
              <div className="load-error" role="alert">
                <p>{error || "A sample timetable could not be generated."}</p>
                <button className="button button-dark" type="button" onClick={() => setActiveView("intake")}>Open planner details</button>
              </div>
            )}
          </div>
        )}
      </main>
      <footer className="site-footer"><span>STUDY SCHEDULER</span><span>Built around your real week.</span></footer>
    </div>
  );
}