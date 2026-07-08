import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet-care planning assistant — add pets, schedule tasks, get a smart daily plan.")

# --- persistent state ---------------------------------------------------------
# Streamlit re-runs this whole script on every interaction, so the Owner is kept
# in st.session_state instead of being recreated (and wiped) each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- add a pet ----------------------------------------------------------------
st.subheader("1. Add a pet")
with st.form("add_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Biscuit")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if owner.get_pet(pet_name):
            st.warning(f"{pet_name} already exists.")
        else:
            owner.add_pet(Pet(pet_name, species))
            st.success(f"Added {pet_name} the {species}.")

pet_names = [p.name for p in owner.pets]

# --- add a task ---------------------------------------------------------------
st.subheader("2. Schedule a task")
if not pet_names:
    st.info("Add a pet first.")
else:
    with st.form("add_task", clear_on_submit=True):
        target = st.selectbox("For which pet?", pet_names)
        desc = st.text_input("Task", value="Morning walk")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            task_time = st.text_input("Time (HH:MM)", value="08:00")
        with c2:
            duration = st.number_input("Minutes", min_value=1, max_value=240, value=30)
        with c3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with c4:
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            pet = owner.get_pet(target)
            pet.add_task(Task(desc, task_time, int(duration), priority, frequency))
            st.success(f"Added '{desc}' at {task_time} for {target}.")

# --- daily plan ---------------------------------------------------------------
st.divider()
st.subheader("3. Today's plan")

view = st.radio("Order by", ["Time", "Priority"], horizontal=True)
tasks = scheduler.sort_by_time() if view == "Time" else scheduler.sort_by_priority()

if not tasks:
    st.info("No tasks yet.")
else:
    pet_of = {id(t): p.name for p, t in owner.all_tasks()}
    rows = [
        {
            "Time": t.time,
            "Task": t.description,
            "Pet": pet_of[id(t)],
            "Min": t.duration_minutes,
            "Priority": t.priority,
            "Repeats": t.frequency,
            "Done": "✅" if t.completed else "⬜",
        }
        for t in tasks
    ]
    st.table(rows)

    # Conflict warnings surfaced prominently for the owner.
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts. 🎉")

# --- complete a task (shows recurring behavior) -------------------------------
st.divider()
st.subheader("4. Mark a task complete")
pending = [(p, t) for p, t in owner.all_tasks() if not t.completed]
if pending:
    labels = [f"{p.name}: {t.time} {t.description}" for p, t in pending]
    choice = st.selectbox("Pick a task", range(len(labels)), format_func=lambda i: labels[i])
    if st.button("Complete task"):
        pet, task = pending[choice]
        nxt = scheduler.complete_task(pet, task)
        if nxt is not None:
            st.success(f"Done! Next '{nxt.description}' auto-scheduled for {nxt.due_date}.")
        else:
            st.success("Task completed.")
        st.rerun()
else:
    st.info("Nothing pending.")
