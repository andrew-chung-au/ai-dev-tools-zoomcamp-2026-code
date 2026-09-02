# Household Chores Tool — Project Plan

## Problem
People forget whose turn it is to do a given chore. The tool exists to make
chore rotation and ownership unambiguous at a glance.

## Scope
- Single household only — no accounts, no login, no multi-household support.
- Access works two ways, both must be supported:
  - A shared device/screen (e.g. a tablet mounted on the fridge)
  - Individual access from each person's own phone or browser

## Rotation Logic
- A chore stays assigned to the same person until it is marked done.
- Marking a chore done rotates it to the next person in the sequence.
- There is no automatic time-based rotation — an undone chore does not move
  on simply because a scheduled interval has passed.

## Overdue Handling
- Overdue chores get a visual indicator only (e.g. highlighted or red).
- No push notifications, email, or other alerts in this version.

## Household & Chore Setup
- Full CRUD: people and chores can be added, edited, and removed at any time.
- No separate one-time setup flow — management is ongoing.

## Open Questions (not yet decided)
- What information does a chore need beyond name? (e.g. frequency, difficulty/weight)
- How are ties or skips handled (e.g. someone unavailable for their turn)?
- Order/algorithm for rotation among multiple people (fixed list order? weighted by difficulty?)

## Status
Core scope settled via brainstorming session. Ready to move into Django
project setup and backlog creation (see Homework 1, Questions 3–4).
