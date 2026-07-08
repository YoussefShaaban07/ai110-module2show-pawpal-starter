"""
Automated tests for the PawPal+ logic layer.

Covers the behaviors that matter most: task completion, task addition,
chronological sorting, recurrence, conflict detection, and a couple of
edge cases (empty pet, no conflicts).
"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler


# --- fixtures -----------------------------------------------------------------

@pytest.fixture
def owner_with_pets():
    """An owner with two pets and a few out-of-order tasks."""
    owner = Owner("Jordan")
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    biscuit.add_task(Task("Evening walk", "18:00", 30, "high", "daily"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high", "daily"))
    mochi.add_task(Task("Litter change", "12:00", 5, "medium", "daily"))
    return owner


# --- task completion ----------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Feeding", "08:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


# --- task addition ------------------------------------------------------------

def test_adding_task_increases_pet_task_count():
    pet = Pet("Biscuit", "dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Walk", "08:00"))
    assert pet.task_count() == 1


# --- sorting ------------------------------------------------------------------

def test_sort_by_time_is_chronological(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    times = [t.time for t in scheduler.sort_by_time()]
    assert times == ["08:00", "12:00", "18:00"]


def test_sort_by_priority_puts_high_first(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    first = scheduler.sort_by_priority()[0]
    assert first.priority == "high"


# --- filtering ----------------------------------------------------------------

def test_filter_by_pet_returns_only_that_pet(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 1
    assert mochi_tasks[0].description == "Litter change"


def test_filter_by_status_separates_done_and_pending(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    scheduler.all_tasks()[0].mark_complete()
    assert len(scheduler.filter_by_status(completed=True)) == 1
    assert len(scheduler.filter_by_status(completed=False)) == 2


# --- recurrence ---------------------------------------------------------------

def test_completing_daily_task_creates_next_day(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    biscuit = owner_with_pets.get_pet("Biscuit")
    morning = next(t for t in biscuit.tasks if t.description == "Morning walk")

    before = biscuit.task_count()
    nxt = scheduler.complete_task(biscuit, morning)

    assert morning.completed is True
    assert nxt is not None
    assert nxt.completed is False
    assert nxt.due_date == morning.due_date + timedelta(days=1)
    assert biscuit.task_count() == before + 1  # a new occurrence was added


def test_once_task_does_not_recur():
    pet = Pet("Mochi", "cat")
    owner = Owner("Jordan")
    owner.add_pet(pet)
    play = Task("Play time", "17:30", 15, "low", "once")
    pet.add_task(play)

    scheduler = Scheduler(owner)
    nxt = scheduler.complete_task(pet, play)
    assert nxt is None
    assert pet.task_count() == 1


def test_weekly_task_recurs_seven_days_later():
    task = Task("Vet checkup", "09:00", 60, "high", "weekly", due_date=date(2026, 1, 1))
    nxt = task.next_occurrence()
    assert nxt.due_date == date(2026, 1, 8)


# --- conflict detection -------------------------------------------------------

def test_detect_conflicts_flags_same_time(owner_with_pets):
    biscuit = owner_with_pets.get_pet("Biscuit")
    biscuit.add_task(Task("Feeding", "08:00", 10, "high", "daily"))  # clashes 08:00
    scheduler = Scheduler(owner_with_pets)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_no_conflicts_when_times_differ(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    assert scheduler.detect_conflicts() == []


def test_completed_tasks_do_not_conflict(owner_with_pets):
    biscuit = owner_with_pets.get_pet("Biscuit")
    feeding = Task("Feeding", "08:00", 10, "high", "daily")
    biscuit.add_task(feeding)
    feeding.mark_complete()  # finished task should not clash
    scheduler = Scheduler(owner_with_pets)
    assert scheduler.detect_conflicts() == []


# --- edge cases ---------------------------------------------------------------

def test_empty_pet_has_no_tasks():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Ghost", "cat"))
    scheduler = Scheduler(owner)
    assert scheduler.all_tasks() == []
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
