# Feature Specification: Server Background Mode & Frontend Redesign

**Feature Branch**: `014-server-background-redesign`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "`uv run frago server` runs server in background mode (daemon), unless --debug flag is used. Default port is 8093 only. Web page at 127.0.0.1:8093 requires complete frontend redesign following FRONTEND_STYLE_GUIDE.md from Agentic-LLM project. Layout uses mainstream admin panel style with collapsible left sidebar menu. Menu order: Dashboard (new), Tasks, Recipes, Skills, Settings. Default landing page is Tasks. All pages retain existing GUI functionality except Dashboard which needs new design (replaces Tips)."

## Clarifications

### Session 2025-12-23

- Q: How should `frago server` implement "background mode" on Windows? → A: Windows runs as a hidden-window subprocess, functionally equivalent to Unix daemon mode

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Server in Background Mode (Priority: P1)

A user wants to start the Frago web service and have it run persistently in the background while they continue working on other tasks in their terminal. They run `uv run frago server` and the command returns immediately to the shell prompt, with the server running as a daemon process accessible at port 8093.

**Why this priority**: Background daemon mode is the core behavioral change that enables persistent service operation. Without this, users must keep a terminal open dedicated to the server process.

**Independent Test**: Can be fully tested by running `frago server`, verifying the command returns to prompt within 3 seconds, and confirming the web service responds at http://127.0.0.1:8093

**Acceptance Scenarios**:

1. **Given** no Frago server is running, **When** user runs `frago server`, **Then** the command returns to prompt within 3 seconds AND server process runs in background AND http://127.0.0.1:8093 responds
2. **Given** a Frago server is already running on port 8093, **When** user runs `frago server`, **Then** user sees a message indicating server is already running with its process ID
3. **Given** server is running in background, **When** user wants to stop the server, **Then** user can run `frago server stop` to terminate the background process

---

### User Story 2 - Navigate Admin Panel Layout (Priority: P1)

A user accesses the Frago web interface at http://127.0.0.1:8093 and sees a professional dark-themed admin panel with a collapsible left sidebar menu containing five navigation items: Dashboard, Tasks, Recipes, Skills, and Settings. The interface automatically opens on the Tasks page.

**Why this priority**: The admin panel layout is the primary user interface change. It must be functional for all subsequent page-specific features to be usable.

**Independent Test**: Can be fully tested by opening http://127.0.0.1:8093, verifying the sidebar exists with all five menu items, clicking each menu item to confirm navigation works, and confirming Tasks page is shown by default

**Acceptance Scenarios**:

1. **Given** user opens http://127.0.0.1:8093 for the first time, **When** page loads, **Then** user sees Tasks page as the default view with sidebar showing Dashboard, Tasks, Recipes, Skills, Settings menu items in that order
2. **Given** user is on any page, **When** user clicks a different menu item in sidebar, **Then** the corresponding page content loads without full page refresh
3. **Given** user has sidebar expanded, **When** user clicks the collapse button, **Then** sidebar collapses to icon-only mode while preserving all navigation functionality
4. **Given** user has sidebar collapsed, **When** user clicks expand button OR hovers over sidebar, **Then** sidebar expands to show full menu labels

---

### User Story 3 - Run Server in Debug Mode (Priority: P2)

A developer needs to debug the Frago server and wants to see all logs in real-time. They run `frago server --debug` and the server runs in foreground mode with verbose output displayed in the terminal, blocking the terminal until stopped with Ctrl+C.

**Why this priority**: Debug mode is essential for development and troubleshooting but is not required for normal user operation.

**Independent Test**: Can be fully tested by running `frago server --debug`, verifying terminal shows live logs and does not return to prompt, then pressing Ctrl+C to confirm graceful shutdown

**Acceptance Scenarios**:

1. **Given** user runs `frago server --debug`, **When** server starts, **Then** terminal shows verbose log output AND does not return to prompt AND server listens on port 8093
2. **Given** server is running in debug mode, **When** requests are made to the server, **Then** request details appear in terminal output
3. **Given** server is running in debug mode, **When** user presses Ctrl+C, **Then** server shuts down gracefully with cleanup message

---

### User Story 4 - Manage Tasks from Redesigned Page (Priority: P2)

A user opens the Tasks page and can view all existing tasks, create new tasks by entering descriptions, and click on individual tasks to see their details. The page functionality matches the existing GUI Tasks page but with the new dark theme styling.

**Why this priority**: Tasks page is the default landing page and core functionality. Maintaining feature parity ensures no regression.

**Independent Test**: Can be fully tested by creating a new task, viewing the task list, clicking a task to see details, and comparing functionality with current --gui mode

**Acceptance Scenarios**:

1. **Given** user is on Tasks page with no existing tasks, **When** page loads, **Then** user sees empty state message and input area for new task description
2. **Given** user enters task description and submits, **When** task is created, **Then** new task appears in task list AND input clears
3. **Given** tasks exist in the list, **When** user clicks a task card, **Then** task detail view opens showing full task information

---

### User Story 5 - Browse Recipes with New Design (Priority: P2)

A user opens the Recipes page and can view all available recipes with search/filter functionality. Clicking a recipe shows its details. All functionality matches existing GUI but with new dark theme styling.

**Why this priority**: Recipes page is a core feature for managing automation scripts. Feature parity is required.

**Independent Test**: Can be fully tested by viewing recipe list, using search to filter, clicking a recipe to view details

**Acceptance Scenarios**:

1. **Given** user is on Recipes page, **When** page loads, **Then** user sees list of all available recipes grouped by category (Atomic/Workflow) with source tags
2. **Given** recipes exist, **When** user types in search box, **Then** recipe list filters in real-time by name and tags
3. **Given** user clicks on a recipe card, **When** clicked, **Then** recipe detail view opens showing full recipe information

---

### User Story 6 - View Skills with New Design (Priority: P2)

A user opens the Skills page and can view all registered skills with their names, descriptions, and file paths. Functionality matches existing GUI with new styling.

**Why this priority**: Skills page displays important information but has simpler functionality than Tasks or Recipes.

**Independent Test**: Can be fully tested by viewing skills list and verifying all skill information displays correctly

**Acceptance Scenarios**:

1. **Given** user is on Skills page with registered skills, **When** page loads, **Then** user sees list of skills showing name, description, and file path for each
2. **Given** no skills are registered, **When** page loads, **Then** user sees empty state with guidance message

---

### User Story 7 - Configure Settings with New Design (Priority: P2)

A user opens the Settings page and can configure all Frago settings including General, Sync, Secrets, Appearance, and About sections. Functionality matches existing GUI with new styling.

**Why this priority**: Settings page provides important configuration options. Feature parity ensures users can manage their preferences.

**Independent Test**: Can be fully tested by navigating through all settings sections and verifying each option functions correctly

**Acceptance Scenarios**:

1. **Given** user is on Settings page, **When** page loads, **Then** user sees all settings sections: General, Sync, Secrets, Appearance, About
2. **Given** user modifies a setting, **When** change is saved, **Then** setting persists across page refreshes and server restarts

---

### User Story 8 - View Dashboard Overview (Priority: P3)

A user opens the Dashboard page and sees an overview of their Frago environment including system status, recent activity summary, quick action shortcuts, and resource statistics. This replaces the Tips page from the original GUI.

**Why this priority**: Dashboard provides valuable overview information but is not required for core functionality. Users can still use Tasks, Recipes, and Skills pages without it.

**Independent Test**: Can be fully tested by navigating to Dashboard and verifying all dashboard widgets display appropriate information

**Acceptance Scenarios**:

1. **Given** user navigates to Dashboard, **When** page loads, **Then** user sees system status indicating server health and connection status
2. **Given** tasks have been executed, **When** user views Dashboard, **Then** recent activity section shows summary of recent task executions
3. **Given** recipes and skills exist, **When** user views Dashboard, **Then** statistics section shows count of recipes and skills
4. **Given** user sees a quick action on Dashboard, **When** user clicks it, **Then** user is navigated to the appropriate page or action is triggered

---

### Edge Cases

- What happens when port 8093 is already in use by another application?
  - Server displays clear error message with the conflicting process name if detectable
  - Server does NOT automatically find an alternative port (fixed port 8093 only)

- What happens when user runs `frago server` while server is already running?
  - Server detects existing process and displays message with PID
  - No duplicate server process is started

- What happens when user closes browser while server is running?
  - Server continues running in background, accessible when browser reopens

- What happens when system reboots?
  - Server does not auto-start (no system service registration)
  - User must manually run `frago server` again

- What happens when websocket connection drops?
  - Frontend displays connection status indicator
  - Frontend attempts automatic reconnection

- What happens when sidebar is collapsed on mobile/narrow viewport?
  - Sidebar behavior respects responsive design breakpoints
  - On narrow viewports, sidebar defaults to collapsed state

- What happens on Windows when running `frago server`?
  - Server spawns as a hidden-window subprocess (no console window visible)
  - `frago server stop` and `frago server status` work identically to Unix
  - Process is visible in Task Manager for manual termination if needed

## Requirements *(mandatory)*

### Functional Requirements

#### Server Behavior

- **FR-001**: System MUST run the web server as a background daemon process by default when `frago server` is executed
- **FR-002**: System MUST run the web server in foreground mode with verbose logging when `--debug` flag is provided
- **FR-003**: System MUST listen exclusively on port 8093 (no configurable port option)
- **FR-004**: System MUST provide `frago server stop` command to terminate background server process
- **FR-005**: System MUST provide `frago server status` command to check if server is running and display its PID
- **FR-006**: System MUST prevent starting duplicate server instances on the same port
- **FR-007**: System MUST display clear error message when port 8093 is unavailable
- **FR-008**: System MUST bind to 127.0.0.1 only for security (localhost access only)

#### Frontend Layout

- **FR-010**: Frontend MUST use dark theme following FRONTEND_STYLE_GUIDE.md specifications exactly
- **FR-011**: Frontend MUST display collapsible left sidebar with navigation menu
- **FR-012**: Sidebar menu MUST contain exactly five items in order: Dashboard, Tasks, Recipes, Skills, Settings
- **FR-013**: Frontend MUST default to Tasks page on initial load
- **FR-014**: Sidebar MUST support collapse to icon-only mode and expand to full-label mode
- **FR-015**: Frontend MUST use CSS variables as defined in FRONTEND_STYLE_GUIDE.md (no hardcoded colors)
- **FR-016**: Frontend MUST support responsive design for different viewport sizes
- **FR-017**: Frontend MUST maintain websocket connection for real-time updates with reconnection handling

#### Page Functionality

- **FR-020**: Tasks page MUST provide all functionality of current GUI Tasks page (list, create, view detail)
- **FR-021**: Recipes page MUST provide all functionality of current GUI Recipes page (list, search, filter, view detail)
- **FR-022**: Skills page MUST provide all functionality of current GUI Skills page (list, view details)
- **FR-023**: Settings page MUST provide all functionality of current GUI Settings page (General, Sync, Secrets, Appearance, About sections)
- **FR-024**: Dashboard page MUST display system status, recent activity, and resource statistics
- **FR-025**: Dashboard page MUST provide quick action shortcuts to common tasks

### Key Entities

- **Server Process**: Represents the running web service instance; attributes include PID, port, start time, and running status
- **Navigation State**: Represents current page selection and sidebar collapse state; persists across page interactions
- **Dashboard Metrics**: Represents aggregated statistics including task count, recipe count, skill count, and recent activity items

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Server starts and returns to prompt within 3 seconds when run without --debug flag
- **SC-002**: All five navigation pages load within 1 second of menu click
- **SC-003**: Sidebar collapse/expand animation completes in under 200ms
- **SC-004**: 100% feature parity with existing GUI for Tasks, Recipes, Skills, and Settings pages (all existing functionality works)
- **SC-005**: Dashboard displays accurate real-time metrics that update within 5 seconds of underlying data changes
- **SC-006**: Frontend passes accessibility contrast requirements (4.5:1 for text, 3:1 for UI components)
- **SC-007**: Websocket reconnection succeeds within 10 seconds of connection drop
- **SC-008**: Users can complete common tasks (create task, run recipe, view skills) without consulting documentation

## Assumptions

- Users have Chrome or Firefox browser installed for accessing the web interface
- On Unix-like systems, server runs as a standard daemon process; on Windows, server runs as a hidden-window subprocess with equivalent background behavior
- The existing API endpoints and websocket functionality from the current server implementation remain stable
- FRONTEND_STYLE_GUIDE.md represents the definitive style guide and any conflicts with existing GUI styling should favor the style guide
