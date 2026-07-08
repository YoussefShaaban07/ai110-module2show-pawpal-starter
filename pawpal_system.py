"""
PawPal+ logic layer.

This module is the "brain" of the app. It is pure Python with no Streamlit
imports, so it can be built and verified from the command line (main.py) and
from the test suite before it is ever wired into the UI.

Classes
-------
Task      : a single pet-care activity (walk, feeding, meds, ...).
Pet       : one pet and the list of tasks that belong to it.
Owner     : a person and the pets they look after.
Scheduler : organizes tasks across all of an owner's pets (sort, filter,
            conflict detection, recurring tasks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple

# Priority names mapped to a sortable rank (higher = more urgent).
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

# How far ahead the next occurrence of a recurring task lands.
RECURRENCE_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    """A single pet-care activity scheduled at a given time of day."""

    description: str
    time: str                      # 24h "HH:MM", e.g. "08:00"
    duration_minutes: int = 30
    priority: str = "medium"       # "low" | "medium" | "high"
    frequency: str = "once"        # "once" | "daily" | "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def priority_rank(self) -> int:
        """Numeric rank for the task's priority (unknown -> medium)."""
        return PRIORITY_RANK.get(self.priority.lower(), 2)

    def next_occurrence(self) -> Optional["Task"]:
        """
        Return a fresh Task for the next occurrence of a recurring task,
        or None if this task does not repeat.
        """
        delta = RECURRENCE_DELTA.get(self.frequency.lower())
        if delta is None:
            return None
        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            due_date=self.due_date + delta,
        )

    def __str__(self) -> str:
        status = "done" if self.completed else "todo"
        return (
            f"{self.time} — {self.description} ({self.duration_minutes} min) "
            f"[priority: {self.priority}, {self.frequency}, {status}]"
        )


class Pet:
    """One pet and the tasks that belong to it."""

    def __init__(self, name: str, species: str = "dog") -> None:
        self.name = name
        self.species = species
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def list_tasks(self) -> List[Task]:
        """Return all of this pet's tasks."""
        return list(self.tasks)

    def pending_tasks(self) -> List[Task]:
        """Return only the tasks that are not yet complete."""
        return [t for t in self.tasks if not t.completed]

    def task_count(self) -> int:
        """How many tasks this pet has."""
        return len(self.tasks)

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self.tasks)})"


class Owner:
    """A person who manages one or more pets."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def all_tasks(self) -> List[Tuple[Pet, Task]]:
        """
        Return every task across every pet, paired with its pet so callers
        know who each task belongs to.
        """
        pairs: List[Tuple[Pet, Task]] = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, pets={len(self.pets)})"


class Scheduler:
    """
    The scheduling brain. Works across ALL of an owner's pets, not just one.

    Algorithmic features:
      - sort_by_time / sort_by_priority
      - filter_by_pet / filter_by_status / filter_by_priority
      - detect_conflicts (tasks sharing a time slot)
      - complete_task (marks done and auto-creates the next recurring instance)
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # --- retrieval -----------------------------------------------------------

    def _pairs(self) -> List[Tuple[Pet, Task]]:
        """All (pet, task) pairs across the owner's pets."""
        return self.owner.all_tasks()

    def all_tasks(self) -> List[Task]:
        """Flat list of every task across all pets."""
        return [task for _, task in self._pairs()]

    # --- sorting -------------------------------------------------------------

    def sort_by_time(self) -> List[Task]:
        """Return all tasks sorted chronologically by their HH:MM time."""
        return sorted(self.all_tasks(), key=lambda t: t.time)

    def sort_by_priority(self) -> List[Task]:
        """Return all tasks sorted most-urgent first, then by time."""
        return sorted(
            self.all_tasks(),
            key=lambda t: (-t.priority_rank(), t.time),
        )

    # --- filtering -----------------------------------------------------------

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return tasks belonging to a single pet (case-insensitive)."""
        return [
            task for pet, task in self._pairs()
            if pet.name.lower() == pet_name.lower()
        ]

    def filter_by_status(self, completed: bool) -> List[Task]:
        """Return tasks matching a completion status."""
        return [t for t in self.all_tasks() if t.completed == completed]

    def filter_by_priority(self, priority: str) -> List[Task]:
        """Return tasks matching a priority level."""
        return [
            t for t in self.all_tasks()
            if t.priority.lower() == priority.lower()
        ]

    # --- conflict detection --------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """
        Find tasks that share the same time slot (same or different pets).
        Returns a list of human-readable warning strings (empty if none).
        Only pending tasks are considered — a finished task can't clash.
        """
        by_time: dict[str, List[Tuple[Pet, Task]]] = {}
        for pet, task in self._pairs():
            if task.completed:
                continue
            by_time.setdefault(task.time, []).append((pet, task))

        warnings: List[str] = []
        for time_slot, entries in sorted(by_time.items()):
            if len(entries) > 1:
                who = ", ".join(f"{p.name}: {t.description}" for p, t in entries)
                warnings.append(f"⚠️  Conflict at {time_slot} — {who}")
        return warnings

    # --- recurring tasks -----------------------------------------------------

    def complete_task(self, pet: Pet, task: Task) -> Optional[Task]:
        """
        Mark a task complete. If it is recurring (daily/weekly), automatically
        create the next occurrence, attach it to the same pet, and return it.
        Returns None for one-off tasks.
        """
        task.mark_complete()
        nxt = task.next_occurrence()
        if nxt is not None:
            pet.add_task(nxt)
        return nxt

    # --- presentation --------------------------------------------------------

    def todays_schedule(self) -> str:
        """Build a readable, time-sorted plan across all pets, plus warnings."""
        lines = [f"Today's plan for {self.owner.name}:"]
        pet_of = {id(task): pet for pet, task in self._pairs()}
        for task in self.sort_by_time():
            pet = pet_of[id(task)]
            lines.append(f"  {task}  <{pet.name}>")
        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("")
            lines.extend(conflicts)
        return "\n".join(lines)
