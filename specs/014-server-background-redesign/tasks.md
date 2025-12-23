# Tasks: Server Background Mode & Frontend Redesign

**Input**: Design documents from `/specs/014-server-background-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Paths: Backend `src/frago/`, Frontend `src/frago/gui/frontend/src/`

---

## Phase 1: Setup

**Purpose**: Project structure updates and dependency verification

- [x] T001 Verify Python dependencies (psutil, fastapi, uvicorn) in pyproject.toml
- [x] T002 [P] Verify frontend dependencies (react, zustand, tailwindcss) in src/frago/gui/frontend/package.json
- [x] T003 [P] Create server log directory structure at ~/.frago/ if not exists

---

## Phase 2: Foundational (Backend Infrastructure)

**Purpose**: Core infrastructure that blocks ALL user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create daemon process manager module in src/frago/server/daemon.py with is_server_running(), start_daemon(), stop_daemon() functions
- [x] T005 [P] Update port handling to fixed 8093 in src/frago/server/utils.py (remove port configuration, add port conflict detection)
- [x] T006 [P] Update CORS configuration for port 8093 in src/frago/server/app.py
- [x] T007 Create server command group in src/frago/cli/server_command.py with start/stop/status subcommands
- [x] T008 Register server command group in src/frago/cli/main.py (add to CLI entry point)
- [x] T009 [P] Add deprecation warning to existing serve command in src/frago/cli/serve_command.py

**Checkpoint**: Backend server command infrastructure complete

---

## Phase 3: User Story 1 - Start Server in Background Mode (Priority: P1) 🎯 MVP

**Goal**: `frago server` starts daemon process and returns to prompt within 3 seconds

**Independent Test**: Run `frago server`, verify prompt returns <3s, verify http://127.0.0.1:8093 responds

### Implementation for User Story 1

- [x] T010 [US1] Implement background process spawning in src/frago/server/daemon.py using subprocess.Popen with platform-specific flags (Unix: start_new_session, Windows: CREATE_NO_WINDOW)
- [x] T011 [US1] Implement PID file management (write/read/cleanup) in src/frago/server/daemon.py at ~/.frago/server.pid
- [x] T012 [US1] Implement duplicate server detection in src/frago/server/daemon.py using PID file + psutil process validation
- [x] T013 [US1] Implement `frago server` start subcommand in src/frago/cli/server_command.py with success/already-running/port-conflict messages
- [x] T014 [US1] Implement `frago server stop` subcommand in src/frago/cli/server_command.py with PID-based process termination
- [x] T015 [US1] Implement `frago server status` subcommand in src/frago/cli/server_command.py showing PID, URL, uptime
- [x] T016 [US1] Update server runner in src/frago/server/runner.py to support both daemon and foreground modes

**Checkpoint**: User Story 1 complete - `frago server` works in background mode

---

## Phase 4: User Story 2 - Navigate Admin Panel Layout (Priority: P1)

**Goal**: Professional dark-themed admin panel with collapsible left sidebar containing 5 menu items

**Independent Test**: Open http://127.0.0.1:8093, verify sidebar with 5 items, verify Tasks is default page, verify collapse/expand works

### Implementation for User Story 2

- [x] T017 [P] [US2] Create CSS variables following FRONTEND_STYLE_GUIDE.md in src/frago/gui/frontend/src/styles/globals.css (background, text, button, border colors)
- [x] T018 [P] [US2] Update Tailwind config with style guide colors in src/frago/gui/frontend/tailwind.config.js
- [x] T019 [US2] Create collapsible Sidebar component in src/frago/gui/frontend/src/components/layout/Sidebar.tsx with 5 menu items (Dashboard, Tasks, Recipes, Skills, Settings)
- [x] T020 [US2] Create MainLayout wrapper component in src/frago/gui/frontend/src/components/layout/MainLayout.tsx with sidebar + content area
- [x] T021 [US2] Update appStore with sidebar state (collapsed, currentPage) and localStorage persistence in src/frago/gui/frontend/src/stores/appStore.ts
- [x] T022 [US2] Rewrite App.tsx with MainLayout integration in src/frago/gui/frontend/src/App.tsx (default to Tasks page)
- [x] T023 [US2] Update API base URL to port 8093 in src/frago/gui/frontend/src/api/index.ts
- [x] T024 [US2] Add responsive breakpoints for sidebar in src/frago/gui/frontend/src/components/layout/Sidebar.tsx (collapse on narrow viewports)

**Checkpoint**: User Story 2 complete - Admin panel layout functional with navigation

---

## Phase 5: User Story 3 - Run Server in Debug Mode (Priority: P2)

**Goal**: `frago server --debug` runs in foreground with verbose logging

**Independent Test**: Run `frago server --debug`, verify terminal shows logs and blocks, press Ctrl+C to confirm graceful shutdown

### Implementation for User Story 3

- [x] T025 [US3] Add --debug flag handling in src/frago/cli/server_command.py to bypass daemon mode
- [x] T026 [US3] Implement foreground runner with verbose logging in src/frago/server/runner.py (access_log=True, log_level=debug)
- [x] T027 [US3] Ensure graceful shutdown with cleanup message in src/frago/server/runner.py signal handlers

**Checkpoint**: User Story 3 complete - Debug mode works with live logs

---

## Phase 6: User Story 4 - Manage Tasks from Redesigned Page (Priority: P2)

**Goal**: Tasks page with new dark theme styling, maintaining all existing functionality

**Independent Test**: Create task, view list, click task for details - all with new styling

### Implementation for User Story 4

- [x] T028 [P] [US4] Update TaskList styling in src/frago/gui/frontend/src/components/tasks/TaskList.tsx with style guide colors
- [x] T029 [P] [US4] Update TaskCard styling in src/frago/gui/frontend/src/components/tasks/TaskCard.tsx with style guide colors
- [x] T030 [P] [US4] Update TaskDetail styling in src/frago/gui/frontend/src/components/tasks/TaskDetail.tsx with style guide colors
- [x] T031 [US4] Update StepList styling in src/frago/gui/frontend/src/components/tasks/StepList.tsx with style guide colors

**Checkpoint**: User Story 4 complete - Tasks page restyled

---

## Phase 7: User Story 5 - Browse Recipes with New Design (Priority: P2)

**Goal**: Recipes page with new dark theme styling, maintaining search/filter/detail functionality

**Independent Test**: View recipes, search, click recipe for details - all with new styling

### Implementation for User Story 5

- [x] T032 [P] [US5] Update RecipeList styling in src/frago/gui/frontend/src/components/recipes/RecipeList.tsx with style guide colors
- [x] T033 [US5] Update RecipeDetail styling in src/frago/gui/frontend/src/components/recipes/RecipeDetail.tsx with style guide colors

**Checkpoint**: User Story 5 complete - Recipes page restyled

---

## Phase 8: User Story 6 - View Skills with New Design (Priority: P2)

**Goal**: Skills page with new dark theme styling

**Independent Test**: View skills list with new styling

### Implementation for User Story 6

- [x] T034 [US6] Update SkillList styling in src/frago/gui/frontend/src/components/skills/SkillList.tsx with style guide colors

**Checkpoint**: User Story 6 complete - Skills page restyled

---

## Phase 9: User Story 7 - Configure Settings with New Design (Priority: P2)

**Goal**: Settings page with new dark theme styling for all sections

**Independent Test**: Navigate through General, Sync, Secrets, Appearance, About sections with new styling

### Implementation for User Story 7

- [x] T035 [P] [US7] Update SettingsPage styling in src/frago/gui/frontend/src/components/settings/SettingsPage.tsx with style guide colors
- [x] T036 [P] [US7] Update GeneralSettings styling in src/frago/gui/frontend/src/components/settings/GeneralSettings.tsx
- [x] T037 [P] [US7] Update SyncSettings styling in src/frago/gui/frontend/src/components/settings/SyncSettings.tsx
- [x] T038 [P] [US7] Update SecretsSettings styling in src/frago/gui/frontend/src/components/settings/SecretsSettings.tsx
- [x] T039 [P] [US7] Update AppearanceSettings styling in src/frago/gui/frontend/src/components/settings/AppearanceSettings.tsx
- [x] T040 [P] [US7] Update AboutSettings styling in src/frago/gui/frontend/src/components/settings/AboutSettings.tsx

**Checkpoint**: User Story 7 complete - Settings page restyled

---

## Phase 10: User Story 8 - View Dashboard Overview (Priority: P3)

**Goal**: New Dashboard page with system status, recent activity, resource stats, quick actions

**Independent Test**: Navigate to Dashboard, verify all widgets display data

### Implementation for User Story 8

- [x] T041 [US8] Create dashboard API route in src/frago/server/routes/dashboard.py implementing GET /api/dashboard
- [x] T042 [US8] Register dashboard router in src/frago/server/app.py
- [x] T043 [US8] Create DashboardPage component in src/frago/gui/frontend/src/components/dashboard/DashboardPage.tsx with system status widget
- [x] T044 [US8] Add recent activity widget to DashboardPage in src/frago/gui/frontend/src/components/dashboard/DashboardPage.tsx
- [x] T045 [US8] Add resource statistics widget (task/recipe/skill counts) to DashboardPage
- [x] T046 [US8] Add quick action shortcuts to DashboardPage (navigate to create task, view recipes, etc.)
- [x] T047 [US8] Add dashboard API client function in src/frago/gui/frontend/src/api/index.ts

**Checkpoint**: User Story 8 complete - Dashboard page functional

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and improvements

- [x] T048 [P] Update StatusBar component for new layout in src/frago/gui/frontend/src/components/layout/StatusBar.tsx
- [x] T049 [P] Update EmptyState component styling in src/frago/gui/frontend/src/components/ui/EmptyState.tsx
- [x] T050 [P] Update Toast component styling in src/frago/gui/frontend/src/components/ui/Toast.tsx
- [x] T051 [P] Update Modal component styling in src/frago/gui/frontend/src/components/ui/Modal.tsx
- [x] T052 [P] Update LoadingSpinner component styling in src/frago/gui/frontend/src/components/ui/LoadingSpinner.tsx
- [x] T053 Build frontend assets: cd src/frago/gui/frontend && pnpm build
- [ ] T054 Run quickstart.md validation - manual end-to-end test
- [x] T055 Remove TipsPage component if no longer needed in src/frago/gui/frontend/src/components/tips/TipsPage.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational (Phase 2)
  - US1 and US2 are both P1 and can run in parallel
  - US3-US7 are P2 and can run in parallel after US1/US2
  - US8 is P3, can start after Foundational
- **Polish (Phase 11)**: Depends on all user stories complete

### User Story Dependencies

| Story | Priority | Depends On | Can Parallel With |
|-------|----------|------------|-------------------|
| US1 (Background Server) | P1 | Foundational | US2 |
| US2 (Admin Panel Layout) | P1 | Foundational | US1 |
| US3 (Debug Mode) | P2 | US1 | US4-US8 |
| US4 (Tasks Restyle) | P2 | US2 | US3, US5-US8 |
| US5 (Recipes Restyle) | P2 | US2 | US3, US4, US6-US8 |
| US6 (Skills Restyle) | P2 | US2 | US3-US5, US7-US8 |
| US7 (Settings Restyle) | P2 | US2 | US3-US6, US8 |
| US8 (Dashboard) | P3 | US2 | US3-US7 |

### Within Each User Story

- Backend tasks before frontend tasks that depend on them
- Shared infrastructure before specific features
- [P] tasks within same story can run in parallel

---

## Parallel Execution Examples

### Phase 2: Foundational (T004-T009)

```bash
# Sequential: T004 first (daemon.py is core)
Task T004: Create daemon process manager

# Then parallel:
Task T005: Update port handling in utils.py
Task T006: Update CORS in app.py
Task T009: Add deprecation to serve_command.py

# Then:
Task T007: Create server command group (depends on T004, T005)
Task T008: Register in main.py (depends on T007)
```

### Phase 4: User Story 2 (T017-T024)

```bash
# Parallel (independent files):
Task T017: Create CSS variables in globals.css
Task T018: Update Tailwind config

# Then:
Task T019: Create Sidebar component (depends on T017, T18)
Task T020: Create MainLayout (depends on T17, T18)
Task T021: Update appStore

# Then:
Task T022: Rewrite App.tsx (depends on T19, T20, T21)
Task T023: Update API URL
Task T024: Add responsive breakpoints
```

### Phase 9: User Story 7 (T035-T040)

```bash
# All parallel (different files, same styling changes):
Task T035: Update SettingsPage.tsx
Task T036: Update GeneralSettings.tsx
Task T037: Update SyncSettings.tsx
Task T038: Update SecretsSettings.tsx
Task T039: Update AppearanceSettings.tsx
Task T040: Update AboutSettings.tsx
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Background Server)
4. Complete Phase 4: US2 (Admin Panel)
5. **STOP and VALIDATE**: Server runs in background, admin panel navigates
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 + US2 → MVP (server + layout)
3. US3 → Debug mode for developers
4. US4-US7 → Page restyling (feature parity)
5. US8 → Dashboard (nice-to-have)
6. Polish → Final cleanup

### Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|------------------------|
| 1: Setup | 3 | 2 |
| 2: Foundational | 6 | 3 |
| 3: US1 | 7 | 0 |
| 4: US2 | 8 | 2 |
| 5: US3 | 3 | 0 |
| 6: US4 | 4 | 3 |
| 7: US5 | 2 | 1 |
| 8: US6 | 1 | 0 |
| 9: US7 | 6 | 6 |
| 10: US8 | 7 | 0 |
| 11: Polish | 8 | 5 |
| **Total** | **55** | **22** |

---

## Notes

- Tests not included (not requested in spec, manual testing pattern per plan.md)
- [P] tasks can run in parallel within their phase
- Commit after each task or logical group
- Frontend build (T053) required before final validation
- TipsPage removal (T055) is optional cleanup after Dashboard confirmed working
