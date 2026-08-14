# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-hosted app for tracking study programs (Studiengänge), modules
(Module), grades and weekly exercise-sheet submissions (Klausurzulassung)
across a double-degree / multi-program setup. Two-service monorepo:
Flask REST API (`backend/`) + Next.js frontend (`frontend/`), wired together
only via JSON over HTTP — no shared code, no code generation between them.

## Commands

```bash
# Full stack (from repo root)
docker compose up --build          # frontend :3001, backend :5001
docker compose exec backend python seed.py   # demo data (no-ops if DB non-empty)

# Backend, without Docker
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
FLASK_APP=wsgi.py flask run --port 5001

# Backend tests
cd backend
python -m pytest                                   # all tests (use `python -m`, not bare `pytest` — see note below)
python -m pytest tests/test_grading.py -q           # one file
python -m pytest tests/test_grading.py::TestBestGrade -q   # one class/test

# Frontend, without Docker
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:5001 npm run dev
npm run build   # also type-checks (tsc runs as part of `next build`)
npm run lint
```

Notes:
- `python -m pytest` (not bare `pytest`) is required from `backend/` because
  there's no `pyproject.toml`/`pytest.ini` adding `backend/` to `sys.path`;
  `-m` implicitly adds the cwd so `from app import ...` resolves.
- Backend ports are non-default (**5001** host → container 5000) because
  ports 3000/5000 are already used by an unrelated `modul_planer` container
  stack on the target machine — don't "fix" this back to 3000/5000 without
  checking for that conflict first. Frontend is host **3001** → container 3000.
- `NEXT_PUBLIC_API_URL` is inlined into the frontend bundle at **build time**
  (Next.js behavior for `NEXT_PUBLIC_*` vars) — changing the backend URL
  requires rebuilding the frontend image/dev server, not just restarting it.
- No migrations (no Alembic). Schema changes require deleting the SQLite
  file/volume in dev (`rm backend/instance/grades.db` or
  `docker volume rm grade_tracker_backend-data`) — `db.create_all()` runs on
  every app startup but never alters existing tables.

## Architecture

### Backend: business logic is deliberately separate from the DB/web layer

`backend/app/grading.py` holds all grading/progress calculations as pure
functions/dataclasses with **no Flask or SQLAlchemy imports**. `models.py`
(SQLAlchemy) calls into `grading.py` from `to_dict()` methods to compute
`final_grade`, `zulassung`, and series `progress` **at serialization time** —
these are never persisted columns. When changing grading rules, edit
`grading.py` (covered by `tests/test_grading.py`) rather than adding computed
columns to models. Route handlers in `app/routes/*.py` stay thin: parse/validate
request JSON, touch the DB, return `model.to_dict()`.

Domain rules encoded in `grading.py` (not obvious from the schema alone):
- A `Modul` has up to 3 `GradeAttempt`s (slots 1–3, upserted by slot via
  `POST /module/<id>/grades`). The **best** (lowest numeric, German scale)
  wins; a numeric attempt always beats pass/fail attempts.
- Pass/fail-graded modules count toward credit totals but are **excluded**
  from the credit-weighted average.
- A module's Klausurzulassung requires **all** of its `SubmissionSeries` to
  individually clear their `threshold_percent` (AND, not OR) — a module with
  zero series is trivially "zugelassen".
- `KombiModul` (M:N with `Modul` via the `kombimodul_module` table) always
  requires its own `studiengang_id` (unlike `Modul.studiengang_id`, which is
  nullable = "Sonstiges"). Its grade is the arithmetic mean of its source
  modules' final grades, and only resolves once *every* source module has a
  numeric final grade.

Blueprints are registered in `app/__init__.py:create_app()`; add new routes
there. `app/stats.py`-style aggregation (`routes/stats.py`) reuses
`grading.weighted_average`/`kombimodul_grade` rather than recomputing sums
inline — follow that pattern for new aggregate endpoints.

### Frontend: client-fetched, no server-side data fetching

Every page under `frontend/src/app/` is a `"use client"` component that
fetches through `frontend/src/lib/api.ts` (a single typed fetch wrapper) in
`useEffect`, keeping the whole app on one consistent data-fetching pattern
(mutation-heavy CRUD app, so server components/SSR fetching were skipped on
purpose). `frontend/src/lib/types.ts` mirrors the backend's JSON response
shapes **by hand** — there's no schema codegen, so a backend response-shape
change means updating `types.ts` (and usually `api.ts`) manually.

Design tokens (categorical `series-1`…`series-7`, status colors
`status-good/warning/serious/critical`, surface/text/border roles) are
defined as CSS custom properties in `globals.css` and mapped into Tailwind v4
via `@theme inline`; both a light palette and a `prefers-color-scheme: dark`
override are defined. Reuse these tokens (`bg-series-1`, `text-status-critical`,
etc.) for any new UI instead of introducing new colors.

**`frontend/AGENTS.md`/`frontend/CLAUDE.md`** (auto-generated by `next dev`,
committed intentionally) flags that this Next.js version (16) has breaking
changes vs. typical training data — e.g. `params`/`searchParams` in
`page.tsx` are Promises requiring `use()`/`await`, and the global
`PageProps<'/route'>` helper type is generated by the Next.js typegen.
Check `node_modules/next/dist/docs/` before writing Next-specific code that
looks off.

### Data model

`Studiengang` 1—N `Modul` (nullable FK = "Sonstiges" bucket) and 1—N
`KombiModul`. `Modul` 1—(≤3) `GradeAttempt`, 1—N `SubmissionSeries` 1—N
`Submission`. `KombiModul` M—N `Modul` (≥2 required) via `kombimodul_module`.
Full ER diagram and REST endpoint table are in `README.md`.
