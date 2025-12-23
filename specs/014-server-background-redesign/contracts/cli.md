# CLI Contract: Server Command Group

**Feature**: 014-server-background-redesign

## Command Structure

```
frago server [SUBCOMMAND]
```

## Subcommands

### `frago server` (default: start)

Start the web service in background mode.

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--debug` | flag | false | Run in foreground with verbose logging |

**Behavior**:
- Without `--debug`: Spawns daemon process, returns to prompt within 3 seconds
- With `--debug`: Runs in foreground, blocks terminal, shows live logs

**Exit codes**:
| Code | Meaning |
|------|---------|
| 0 | Server started successfully |
| 1 | Server already running |
| 2 | Port 8093 unavailable |

**Output examples**:

```bash
# Success (background)
$ frago server
Frago server started on http://127.0.0.1:8093 (PID: 12345)

# Already running
$ frago server
Frago server is already running (PID: 12345)

# Port conflict
$ frago server
Error: Port 8093 is in use by chrome (PID: 54321)

# Debug mode
$ frago server --debug
  Frago Web Service (Debug Mode)
  ─────────────────────────────────
  Local:   http://127.0.0.1:8093
  API:     http://127.0.0.1:8093/api/docs

  Press Ctrl+C to stop

[2025-12-23 10:30:00] INFO: Uvicorn running...
```

### `frago server stop`

Stop the running web service.

**Exit codes**:
| Code | Meaning |
|------|---------|
| 0 | Server stopped successfully |
| 1 | Server not running |

**Output examples**:

```bash
# Success
$ frago server stop
Frago server stopped (PID: 12345)

# Not running
$ frago server stop
Frago server is not running
```

### `frago server status`

Check if the web service is running.

**Exit codes**:
| Code | Meaning |
|------|---------|
| 0 | Server is running |
| 1 | Server is not running |

**Output examples**:

```bash
# Running
$ frago server status
Frago server is running
  PID:     12345
  URL:     http://127.0.0.1:8093
  Uptime:  2h 30m

# Not running
$ frago server status
Frago server is not running
```

## Files

| File | Purpose |
|------|---------|
| `~/.frago/server.pid` | Stores PID of running server |
| `~/.frago/server.log` | Server log output (background mode) |

## Deprecation

The existing `frago serve` command will be deprecated in favor of `frago server`. During transition:
- `frago serve` continues to work but shows deprecation warning
- Future version will remove `frago serve`
