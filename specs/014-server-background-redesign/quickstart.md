# Quickstart: Server Background Mode & Frontend Redesign

**Feature**: 014-server-background-redesign

## Overview

This feature introduces:
1. `frago server` command group for background web service management
2. Redesigned admin panel frontend with collapsible sidebar
3. Fixed port 8093 for simplified configuration
4. New Dashboard page replacing Tips

## Getting Started

### 1. Start the Server

```bash
# Background mode (default)
frago server

# Debug mode (foreground with logs)
frago server --debug
```

### 2. Access the Web Interface

Open http://127.0.0.1:8093 in your browser.

### 3. Navigate the Interface

The sidebar provides access to five pages:
- **Dashboard**: System overview and quick actions
- **Tasks**: Create and monitor automation tasks (default page)
- **Recipes**: Browse and manage recipes
- **Skills**: View registered skills
- **Settings**: Configure Frago

Click the collapse button (☰) to minimize the sidebar.

### 4. Stop the Server

```bash
frago server stop
```

## Development Setup

### Backend Changes

Key files to modify:
```
src/frago/cli/server_command.py  # New command group
src/frago/server/daemon.py       # Process management
src/frago/server/runner.py       # Updated runner
```

### Frontend Changes

Build the frontend:
```bash
cd src/frago/gui/frontend
pnpm install
pnpm build
```

Key files:
```
src/components/layout/Sidebar.tsx    # Collapsible sidebar
src/components/layout/MainLayout.tsx # Admin panel layout
src/components/dashboard/DashboardPage.tsx  # New dashboard
src/styles/globals.css               # Style guide colors
```

### Testing

```bash
# Backend tests
pytest tests/

# Manual frontend testing
frago server --debug
# Open http://127.0.0.1:8093
```

## Migration from `frago serve`

| Old Command | New Command |
|-------------|-------------|
| `frago serve` | `frago server` (background) |
| `frago serve --debug` | `frago server --debug` |
| `frago serve -p 8080` | N/A (fixed port 8093) |

## Troubleshooting

### Port 8093 in use
```bash
# Check what's using the port
frago server status
# or
lsof -i :8093  # Linux/macOS
netstat -ano | findstr :8093  # Windows
```

### Server won't start
```bash
# Check for stale PID file
cat ~/.frago/server.pid
# Remove if process doesn't exist
rm ~/.frago/server.pid
```

### Frontend not loading
```bash
# Rebuild frontend
cd src/frago/gui/frontend
pnpm build
```
