"""
PawPal+ CLI demo.

Verifies the logic layer end-to-end from the terminal before it is wired into
the Streamlit UI. Run with:  python main.py
"""

import sys

from pawpal_system import Owner, Pet, Task

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pawpal_system import Scheduler


def build_demo() -> Owner:
    """Create an owner with two pets and several tasks added out of order."""
    owner = Owner("Jordan")

    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Deliberately added out of chronological order to prove sorting works.
    biscuit.add_task(Task("Evening walk", "18:00", 30, "high", "daily"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high", "daily"))
    biscuit.add_task(Task("Feeding", "08:00", 10, "high", "daily"))  # clashes 08:00
    mochi.add_task(Task("Litter change", "12:00", 5, "medium", "daily"))
    mochi.add_task(Task("Play time", "17:30", 15, "low", "once"))

    return owner


def main() -> None:
    owner = build_demo()
    scheduler = Scheduler(owner)

    print("=" * 60)
    print(scheduler.todays_schedule())
    print("=" * 60)

    print("\nSorted by priority (most urgent first):")
    for task in scheduler.sort_by_priority():
        print(f"  {task}")

    print("\nFiltered — only Mochi's tasks:")
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    print("\nConflict check:")
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        print(f"  {warning}")
    if not conflicts:
        print("  No conflicts.")

    print("\nRecurring-task demo — completing Biscuit's daily morning walk:")
    biscuit = owner.get_pet("Biscuit")
    morning = next(t for t in biscuit.tasks if t.description == "Morning walk")
    nxt = scheduler.complete_task(biscuit, morning)
    print(f"  Marked complete: {morning}")
    print(f"  Auto-created next occurrence: {nxt}  (due {nxt.due_date})")

    print("\nPending tasks after completion:")
    for task in scheduler.filter_by_status(completed=False):
        print(f"  {task}")


if __name__ == "__main__":
    main()
