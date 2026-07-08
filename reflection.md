# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started from three user actions: *add a pet*, *schedule a care task*, and
*see today's plan*. That led to four classes:

- **Task** — one care activity (description, time, duration, priority, frequency,
  completion). It owns its own small behaviors: `mark_complete()` and
  `next_occurrence()`.
- **Pet** — a single animal plus the list of tasks that belong to it
  (`add_task`, `list_tasks`, `pending_tasks`, `task_count`).
- **Owner** — a person with many pets; exposes `all_tasks()` so anything above it
  can see every task at once.
- **Scheduler** — the "brain." It takes an `Owner` and works *across all pets*:
  sorting, filtering, conflict detection, and recurring-task handling.

**b. Design changes**

Two changes happened during implementation:

1. Originally `Owner.all_tasks()` returned a flat list of tasks, but the Scheduler
   needed to know *which pet* each task belonged to (for conflict messages and
   per-pet filtering). I changed it to return `(Pet, Task)` pairs. This kept the
   Scheduler from having to reach back into every pet itself.
2. I added a `due_date` field to `Task`. The first draft only had a `"HH:MM"` time,
   but recurring tasks need a real calendar date so `timedelta` can compute the next
   day/week. Time-of-day handles ordering; `due_date` handles recurrence.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers **time of day** (for ordering and conflict detection),
**priority** (`low`/`medium`/`high`, used by `sort_by_priority`), **completion
status** (finished tasks are ignored for conflicts), and **frequency**
(`once`/`daily`/`weekly`). Time and priority mattered most because a pet owner's
first two questions are "what's next?" and "what can't I skip?"

**b. Tradeoffs**

`detect_conflicts()` only flags tasks that share the **exact same start time**. It
does *not* look at duration overlap — a 08:00 task lasting 30 minutes and an 08:15
task are not flagged even though they overlap in real life. I chose exact-match
because it's simple, fast, and easy to explain, and because the app captures a
start time and duration but not hard "must be alone" windows. Duration-aware
overlap detection is the obvious next iteration (noted in the README and tests).

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI coding assistant to brainstorm the class breakdown, draft the Mermaid
UML, and generate the first pass of the `pytest` suite. The most useful prompts were
concrete and referenced my files — e.g. "based on my skeleton in `pawpal_system.py`,
how should `Scheduler` retrieve tasks from an `Owner`'s pets?" — rather than vague
"write me a scheduler" asks.

**b. Judgment and verification**

I did not accept the assistant's first recurrence design. It suggested mutating the
*same* Task object in place (resetting `completed` and bumping the date), which would
have destroyed the history of what was already done. I changed it so
`next_occurrence()` returns a **new** Task and leaves the completed one intact. I
verified the behavior with `test_completing_daily_task_creates_next_day`, which
checks both that the old task stays `completed` and that a new one lands one day
later. I also rejected an over-clever one-line sort the assistant offered because
the explicit `key=lambda t: (-t.priority_rank(), t.time)` version is easier for a
human to read.

---

## 4. Testing and Verification

**a. What you tested**

Task completion, task addition, chronological sorting, priority sorting, per-pet and
per-status filtering, daily/weekly recurrence, one-off tasks *not* recurring, and
conflict detection (including the edge cases: no conflicts when times differ,
completed tasks not clashing, and an empty pet). These matter because they are the
behaviors a user actually depends on and the ones most likely to silently break.

**b. Confidence**

**★★★★☆ (4/5).** All 13 tests pass and the CLI demo behaves correctly. I'd drop the
last star because conflict detection is start-time-only, so I'm confident in what it
*claims* to check but aware it doesn't catch overlapping durations yet. With more
time I'd add duration-overlap tests and a test for many pets at the same slot.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow. Building and verifying `pawpal_system.py` through `main.py`
and tests *before* touching Streamlit meant the UI wiring in `app.py` was almost
trivial — it just calls methods that were already proven.

**b. What you would improve**

Duration-aware conflict detection, and letting the Scheduler actually *fit* tasks
into free time windows rather than just reporting on the times the user picked.

**c. Key takeaway**

Being the "lead architect" meant the AI was fastest at *filling in* a structure I had
already decided on, and least trustworthy when I let it decide the structure. Keeping
the data model (especially the recurrence design) as a human decision, and using AI
for scaffolding and tests, produced the cleanest result.
