# Research: Server Background Mode & Frontend Redesign

**Date**: 2025-12-23
**Feature**: 014-server-background-redesign

## Research Topics

### 1. Python Daemon Process Management (Cross-Platform)

**Decision**: Use `subprocess.Popen` with platform-specific flags for background execution

**Rationale**:
- Python's `subprocess` module is cross-platform and well-supported
- Unix: Use `start_new_session=True` to detach from terminal
- Windows: Use `CREATE_NO_WINDOW` flag via `creationflags` parameter
- Simpler than `python-daemon` library which is Unix-only
- Avoid systemd/launchd service registration (too complex for single-user tool)

**Alternatives considered**:
- `python-daemon` library: Unix-only, rejected for cross-platform requirement
- `multiprocessing.Process`: Doesn't properly detach, still tied to parent
- Windows Service: Requires admin privileges and registration, too heavy
- `nohup` wrapper: Unix-only, not programmatic

**Implementation pattern**:
```python
# Unix
subprocess.Popen(
    [sys.executable, "-m", "frago.server.runner", "--port", "8093"],
    start_new_session=True,
    stdout=open(log_file, 'a'),
    stderr=subprocess.STDOUT,
)

# Windows
subprocess.Popen(
    [sys.executable, "-m", "frago.server.runner", "--port", "8093"],
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    stdout=open(log_file, 'a'),
    stderr=subprocess.STDOUT,
)
```

### 2. PID File Management for Server Status/Stop

**Decision**: Store PID in `~/.frago/server.pid` with lock file validation

**Rationale**:
- Standard Unix convention for daemon management
- Simple file-based approach works cross-platform
- Use `psutil` (already a dependency) to verify process is still running
- Lock file prevents stale PID issues

**Alternatives considered**:
- SQLite database: Overkill for single value
- Named socket: Platform differences complicate implementation
- Port probe only: Can't distinguish Frago from other services on same port

**Implementation pattern**:
```python
PID_FILE = Path.home() / ".frago" / "server.pid"

def is_server_running() -> tuple[bool, int | None]:
    if not PID_FILE.exists():
        return False, None
    pid = int(PID_FILE.read_text().strip())
    try:
        proc = psutil.Process(pid)
        if "frago" in proc.cmdline():
            return True, pid
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    PID_FILE.unlink(missing_ok=True)  # Clean stale PID
    return False, None
```

### 3. React Sidebar Implementation Pattern

**Decision**: CSS-based collapsible sidebar with Zustand state management

**Rationale**:
- Tailwind CSS provides utility classes for smooth transitions
- Zustand already used in project for state management
- CSS transform/width transitions for collapse animation (<200ms requirement)
- localStorage persistence for sidebar state across sessions

**Alternatives considered**:
- Headless UI library: Adds dependency, project prefers minimal deps
- CSS-only (no state): Can't persist preference across page loads
- React Context: Zustand already established in codebase

**Implementation pattern**:
```typescript
// Store
interface AppStore {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

// Sidebar width states
const SIDEBAR_WIDTH = {
  expanded: '240px',
  collapsed: '64px',
};

// CSS transition
className={`transition-all duration-200 ease-in-out ${
  collapsed ? 'w-16' : 'w-60'
}`}
```

### 4. FRONTEND_STYLE_GUIDE.md Integration

**Decision**: Map style guide CSS variables to Tailwind config and global CSS

**Rationale**:
- Style guide provides complete color palette as CSS variables
- Tailwind `extend.colors` can reference CSS variables
- Global CSS sets `:root` variables for non-Tailwind usage
- Ensures exact compliance with style guide

**Key mappings** (from FRONTEND_STYLE_GUIDE.md):
```css
:root {
  --color-background: #000000;
  --color-background-secondary: #0A0A0A;
  --color-background-hover: #1A1A1A;
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #ADADAD;
  --color-text-muted: #888888;
  --color-button-primary: #EDEDED;
  --color-button-text: #0A0A0A;
  --color-border-primary: #EDEDED;
  --color-border-secondary: #1A1A1A;
}
```

### 5. Dashboard Metrics API

**Decision**: Add `/api/dashboard` endpoint aggregating existing data sources

**Rationale**:
- Reuse existing route handlers (tasks, recipes, skills)
- Single API call for dashboard reduces frontend complexity
- Server-side aggregation is efficient

**API contract**:
```json
GET /api/dashboard
Response: {
  "server_status": "running",
  "uptime_seconds": 3600,
  "stats": {
    "task_count": 10,
    "recipe_count": 25,
    "skill_count": 12
  },
  "recent_activity": [
    {"type": "task", "name": "...", "timestamp": "..."}
  ]
}
```

### 6. Port Conflict Detection

**Decision**: Use socket binding test before server start

**Rationale**:
- Fast and reliable port availability check
- Can identify conflicting process using `psutil`
- Provides actionable error message

**Implementation pattern**:
```python
def check_port_available(port: int) -> tuple[bool, str | None]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True, None
    except OSError:
        # Find conflicting process
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid)
                    return False, f"{proc.name()} (PID: {conn.pid})"
                except:
                    pass
        return False, "Unknown process"
```

## Summary

All technical unknowns resolved. Key decisions:
1. Cross-platform daemon via `subprocess.Popen` with platform-specific flags
2. PID file at `~/.frago/server.pid` with `psutil` validation
3. CSS-based sidebar with Zustand state and localStorage persistence
4. Direct CSS variable mapping from FRONTEND_STYLE_GUIDE.md
5. New `/api/dashboard` endpoint for metrics aggregation
6. Socket-based port conflict detection with process identification
