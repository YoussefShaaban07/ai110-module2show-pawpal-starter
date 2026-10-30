# PawPal+

A Streamlit app that plans a pet owner's day: it tracks care tasks across several pets, orders them by time or priority, warns about scheduling conflicts, and automatically re-creates daily and weekly tasks when they're completed.

**Stack:** Python, Streamlit, pytest · **Tests:** 13 passing · Built for CodePath AI110 (Module 2), designed UML-first and then implemented and tested.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py        # the app
python main.py              # CLI demo of the scheduling logic
pytest                      # test suite
```

## How it's built

1. **Designed first:** UML class diagrams for `Owner`, `Pet`, `Task` and `Scheduler` ([draft](diagrams/uml_draft.mmd) and [final](diagrams/uml_final.mmd)).
2. **Logic layer:** `pawpal_system.py` holds all scheduling behavior, with no UI code, so it can be tested on its own.
3. **Tests:** a pytest suite covering sorting, filtering, recurrence and conflict edge cases.
4. **UI:** `app.py` connects the logic layer to Streamlit through `st.session_state`, so data survives Streamlit's re-runs.

Design notes and trade-offs are in [reflection.md](reflection.md).

## ✨ Features

- **Object-oriented core** (`pawpal_system.py`): `Owner` → `Pet` → `Task`, with a
  `Scheduler` that operates across *all* of an owner's pets.
- **Sorting** by time (`Scheduler.sort_by_time`) and by priority
  (`Scheduler.sort_by_priority`).
- **Filtering** by pet, completion status, or priority.
- **Conflict detection** (`Scheduler.detect_conflicts`) — warns when two tasks share
  a time slot instead of crashing.
- **Recurring tasks** — completing a daily/weekly task auto-creates the next
  occurrence (`Scheduler.complete_task` + `Task.next_occurrence`).
- **Streamlit UI** (`app.py`) wired to the logic layer via `st.session_state`.
- **13-test pytest suite** covering the behaviors above plus edge cases.

## 🖥️ Sample Output

Output of `python main.py`:

```
============================================================
Today's plan for Jordan:
  08:00 — Morning walk (30 min) [priority: high, daily, todo]  <Biscuit>
  08:00 — Feeding (10 min) [priority: high, daily, todo]  <Biscuit>
  12:00 — Litter change (5 min) [priority: medium, daily, todo]  <Mochi>
  17:30 — Play time (15 min) [priority: low, once, todo]  <Mochi>
  18:00 — Evening walk (30 min) [priority: high, daily, todo]  <Biscuit>

⚠️  Conflict at 08:00 — Biscuit: Morning walk, Biscuit: Feeding
============================================================

Sorted by priority (most urgent first):
  08:00 — Morning walk (30 min) [priority: high, daily, todo]
  08:00 — Feeding (10 min) [priority: high, daily, todo]
  18:00 — Evening walk (30 min) [priority: high, daily, todo]
  12:00 — Litter change (5 min) [priority: medium, daily, todo]
  17:30 — Play time (15 min) [priority: low, once, todo]

Filtered — only Mochi's tasks:
  12:00 — Litter change (5 min) [priority: medium, daily, todo]
  17:30 — Play time (15 min) [priority: low, once, todo]

Recurring-task demo — completing Biscuit's daily morning walk:
  Marked complete: 08:00 — Morning walk (30 min) [priority: high, daily, done]
  Auto-created next occurrence: 08:00 — Morning walk (30 min) [priority: high, daily, todo]  (due 2026-07-09)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

The suite covers task completion and addition, chronological and priority sorting,
per-pet / per-status filtering, daily & weekly recurrence (and that one-off tasks do
*not* recur), and conflict detection including edge cases (no conflict when times
differ, completed tasks don't clash, empty pet).

Sample test output:

```
============================= test session starts =============================
collected 13 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  7%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED    [ 15%]
tests/test_pawpal.py::test_sort_by_time_is_chronological PASSED           [ 23%]
tests/test_pawpal.py::test_sort_by_priority_puts_high_first PASSED        [ 30%]
tests/test_pawpal.py::test_filter_by_pet_returns_only_that_pet PASSED     [ 38%]
tests/test_pawpal.py::test_filter_by_status_separates_done_and_pending PASSED [ 46%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day PASSED  [ 53%]
tests/test_pawpal.py::test_once_task_does_not_recur PASSED                [ 61%]
tests/test_pawpal.py::test_weekly_task_recurs_seven_days_later PASSED     [ 69%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time PASSED        [ 76%]
tests/test_pawpal.py::test_no_conflicts_when_times_differ PASSED          [ 84%]
tests/test_pawpal.py::test_completed_tasks_do_not_conflict PASSED         [ 92%]
tests/test_pawpal.py::test_empty_pet_has_no_tasks PASSED                  [100%]

============================= 13 passed in 0.03s ==============================
```

**Confidence level: ★★★★☆ (4/5)** — all core behaviors are tested and pass; the one
reservation is that conflict detection is start-time-only (see reflection).

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Chronological by `"HH:MM"`, or high→low priority then time |
| Filtering | `Scheduler.filter_by_pet()`, `filter_by_status()`, `filter_by_priority()` | Narrow tasks across all pets |
| Conflict handling | `Scheduler.detect_conflicts()` | Returns warning strings for tasks sharing a time slot; ignores completed tasks. **Tradeoff:** exact-time match only, not duration overlap |
| Recurring tasks | `Scheduler.complete_task()`, `Task.next_occurrence()` | Completing a daily/weekly task auto-creates the next instance via `timedelta` |

## 📸 Demo Walkthrough

Run the UI with `streamlit run app.py`, then:

1. **Add a pet** — enter a name (e.g. "Biscuit") and species, click *Add pet*. The
   `Owner` is stored in `st.session_state`, so it survives Streamlit's re-runs.
2. **Schedule tasks** — pick the pet, type a task ("Morning walk"), a time
   (`08:00`), duration, priority, and how often it repeats, then *Add task*. Add a
   couple more, including two at the same time to trigger a conflict.
3. **View today's plan** — the table shows every task across all pets. Toggle
   *Order by* between **Time** and **Priority** to re-sort live.
4. **See conflict warnings** — because two tasks share `08:00`, the app shows a
   yellow ⚠️ warning ("Conflict at 08:00 …"); with no clash it shows a green
   "No scheduling conflicts."
5. **Complete a task** — mark Biscuit's daily *Morning walk* done. Because it's a
   daily task, the app confirms the next occurrence was auto-scheduled for tomorrow.

Key `Scheduler` behaviors shown: chronological + priority sorting, cross-pet
conflict detection, and automatic recurrence. A fenced sample of the equivalent CLI
output is in the **Sample Output** section above.

**Screenshot or video** *(optional)*: *(text walkthrough + CLI output above are the
gradable demo)*
