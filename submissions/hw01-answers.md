# Homework 1: AI-Native Developer Workflow

Below are my answers to the homework questions.  
All placeholders are clearly marked so I can update them later.

---

## 1. Which coding agent did you use? *(1 point)*

**Answer:**  
- Claude Code

---

## 2. What are the 2–4 features your spec settled on? *(1 point)*

**Answer:**  
- Rotation tracking that only moves a chore to the next person when marked done  
- No accounts/login — single household scope  
- Works on both shared devices (e.g., fridge tablet) and individual phones/browsers  
- Overdue chores show a visual indicator (highlight/red), no notifications

---

## 3. Which file do you edit to include your app in the Django project? *(1 point)*

**Answer:**  
- settings.py  

---

## 4. What is task 1 in your `backlog.md`? *(1 point)*

**Answer:**  
## 1. Data model
Create `Person` and `Chore` models in the `chores` app.
- `Person`: name (unique within household).
- `Chore`: name, `assigned_to` (FK to Person), `last_done_at`, `done` flag or
  status.
- Rotation order needs a concrete field even before the algorithm is decided
  — e.g. a `Person.order` int or an ordered `rotation` list on `Chore` — so
  later tasks aren't blocked. **Depends on open question:** rotation
  order/algorithm among multiple people. Default to simple fixed list order
  (by `Person.order`) unless told otherwise.
- Leave chore metadata (frequency, difficulty/weight) out of v1 unless the
  open question gets resolved first — add fields only when there's a
  confirmed need.

---

## 5. Which command starts the Django development server? *(1 point)*

**Answer:**  
- `uv run python manage.py runserver`  

---

## 6. Which command runs the tests in the terminal? *(1 point)*

**Answer:**  
- `python manage.py test`  

---


