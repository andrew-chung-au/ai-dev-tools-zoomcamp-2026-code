# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This directory contains no code yet — only planning docs (`docs/plan.md`). It is
the pre-implementation stage of a Django household-chores app (homework 1 of an
AI dev tools course). There is no Django project scaffolded, no dependency
manifest, and no build/lint/test tooling configured yet. Once a Django project
exists here, this file should be updated with the actual setup, run, and test
commands and the real app architecture.

## Product scope (from docs/plan.md)

- Single household only — no accounts, no login, no multi-household support.
- Two access modes must both work: a shared device/screen (e.g. a fridge-mounted
  tablet) and individual access from each person's own phone/browser.
- Rotation: a chore stays assigned to the same person until marked done; marking
  it done rotates it to the next person in sequence. No automatic time-based
  rotation — an undone chore does not move on just because an interval passed.
- Overdue chores get a visual indicator only (e.g. highlighted/red) — no push
  notifications, email, or other alerts.
- People and chores support full CRUD at any time — there is no separate
  one-time setup flow; management is ongoing.

Open questions not yet decided (don't assume answers without checking with the
user or docs/plan.md for updates): what fields a chore needs beyond name (e.g.
frequency, difficulty/weight); how ties/skips are handled when someone is
unavailable for their turn; the rotation order/algorithm among multiple people.
