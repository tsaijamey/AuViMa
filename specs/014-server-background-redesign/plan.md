# Implementation Plan: Server Background Mode & Frontend Redesign

**Branch**: `014-server-background-redesign` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-server-background-redesign/spec.md`

## Summary

This feature transforms the Frago web service from the current `frago serve` foreground command to a new `frago server` command group that runs as a background daemon by default (or foreground with `--debug`). The frontend undergoes a complete redesign adopting a professional admin panel layout with collapsible left sidebar navigation, following the Agentic-LLM FRONTEND_STYLE_GUIDE.md dark theme. The fixed port 8093 replaces the configurable port system.

## Technical Context

**Language/Version**: Python 3.9+ (backend), TypeScript/React 18 (frontend)
**Primary Dependencies**: FastAPI, Uvicorn, Click (backend); React, Zustand, Tailwind CSS, Vite (frontend)
**Storage**: File-based (existing `~/.frago/` directory structure)
**Testing**: pytest (backend), manual testing (frontend - existing pattern)
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Web application (Python backend + React frontend)
**Performance Goals**: Server start <3s, page load <1s, sidebar animation <200ms
**Constraints**: Port fixed at 8093, localhost-only binding, Windows uses hidden-window subprocess
**Scale/Scope**: Single-user local development tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution file is a template without specific project rules. No gates to enforce.

**Status**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/014-server-background-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (Python)
src/frago/
├── cli/
│   ├── main.py                    # Entry point - add server command group
│   └── server_command.py          # NEW: server subcommands (start/stop/status)
├── server/
│   ├── __init__.py
│   ├── app.py                     # FastAPI app factory (update CORS for 8093)
│   ├── runner.py                  # Server runner (modify for daemon mode)
│   ├── daemon.py                  # NEW: Background process management
│   ├── utils.py                   # Utilities (update port handling)
│   ├── websocket.py               # WebSocket manager (unchanged)
│   └── routes/                    # API routes (unchanged)
└── gui/
    └── frontend/                  # React frontend
        ├── src/
        │   ├── App.tsx            # REWRITE: Admin panel layout
        │   ├── main.tsx           # Entry point (minor updates)
        │   ├── styles/
        │   │   └── globals.css    # REWRITE: FRONTEND_STYLE_GUIDE.md variables
        │   ├── components/
        │   │   ├── layout/
        │   │   │   ├── Sidebar.tsx           # NEW: Collapsible sidebar
        │   │   │   ├── MainLayout.tsx        # NEW: Layout wrapper
        │   │   │   └── StatusBar.tsx         # UPDATE: Adapt to new layout
        │   │   ├── dashboard/
        │   │   │   └── DashboardPage.tsx     # NEW: Replace TipsPage
        │   │   ├── tasks/                    # UPDATE: Apply new styling
        │   │   ├── recipes/                  # UPDATE: Apply new styling
        │   │   ├── skills/                   # UPDATE: Apply new styling
        │   │   └── settings/                 # UPDATE: Apply new styling
        │   ├── stores/
        │   │   └── appStore.ts    # UPDATE: Add sidebar state
        │   └── api/
        │       └── index.ts       # UPDATE: Port 8093
        └── tailwind.config.js     # UPDATE: FRONTEND_STYLE_GUIDE.md colors
```

**Structure Decision**: Web application structure with Python backend and React frontend. Backend changes are focused on CLI command restructuring and daemon process management. Frontend undergoes significant UI restructuring while preserving existing component logic.

## Complexity Tracking

> No constitution violations to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
