# Data Model: Server Background Mode & Frontend Redesign

**Date**: 2025-12-23
**Feature**: 014-server-background-redesign

## Entities

### 1. ServerProcess

Represents the running web service instance.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| pid | int | Process ID | Positive integer |
| port | int | Listening port | Fixed: 8093 |
| host | str | Bound host | Fixed: 127.0.0.1 |
| started_at | datetime | Server start timestamp | ISO 8601 format |
| status | enum | Running state | `running`, `stopped`, `error` |

**Storage**: `~/.frago/server.pid` (PID only, other fields derived at runtime)

**State Transitions**:
```
[Not Running] --frago server--> [Starting] --success--> [Running]
                                          --failure--> [Error]
[Running] --frago server stop--> [Stopping] --> [Not Running]
[Running] --process dies--> [Not Running] (stale PID cleanup)
```

### 2. NavigationState (Frontend)

Represents current UI navigation and layout state.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| currentPage | enum | Active page | `dashboard`, `tasks`, `recipes`, `skills`, `settings` |
| sidebarCollapsed | bool | Sidebar state | Default: false |
| selectedTaskId | string? | Selected task for detail view | Optional |
| selectedRecipeId | string? | Selected recipe for detail view | Optional |

**Storage**: Zustand store with localStorage persistence for `sidebarCollapsed`

**Default**: `currentPage = 'tasks'`, `sidebarCollapsed = false`

### 3. DashboardMetrics

Represents aggregated dashboard statistics.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| server_status | enum | Server health | `running`, `degraded`, `error` |
| uptime_seconds | int | Server uptime | Non-negative |
| task_count | int | Total tasks | Non-negative |
| recipe_count | int | Total recipes | Non-negative |
| skill_count | int | Total skills | Non-negative |
| recent_activity | array | Recent events | Max 10 items |

**Storage**: Computed on-demand from existing data sources (no persistent storage)

### 4. RecentActivityItem

Represents a single recent activity event for dashboard.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| type | enum | Activity type | `task_created`, `task_completed`, `recipe_run` |
| name | string | Item name | Non-empty |
| timestamp | datetime | Event time | ISO 8601 format |
| status | enum? | Result status | Optional: `success`, `failure` |

**Storage**: Derived from task execution history

## Relationships

```
ServerProcess (1) --- serves ---> DashboardMetrics (1)
DashboardMetrics (1) --- contains ---> RecentActivityItem (0..10)
NavigationState (1) --- references ---> Tasks, Recipes, Skills (existing entities)
```

## Validation Rules

### ServerProcess
- PID must be valid and process must exist
- Port must be 8093 (fixed)
- Host must be 127.0.0.1 (fixed)

### NavigationState
- currentPage must be one of the five valid pages
- Default page on load is 'tasks'
- selectedTaskId/selectedRecipeId cleared when switching pages

### DashboardMetrics
- All counts must be non-negative integers
- uptime_seconds must match actual server uptime
- recent_activity limited to 10 most recent items

## File Locations

| Entity | Storage Location | Format |
|--------|------------------|--------|
| ServerProcess PID | `~/.frago/server.pid` | Plain text (PID number) |
| Server logs | `~/.frago/server.log` | Plain text |
| NavigationState | Browser localStorage | JSON |
| DashboardMetrics | In-memory (API response) | JSON |
