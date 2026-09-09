"""Find the local HTTP proxy the agent browser should use, if any.

Why this exists: on a network where part of the web is unreachable
without a proxy, a browser launched with no proxy is not "mostly
working" — it silently hangs on whole regions of the internet, for 30
seconds at a time, with no error a caller can act on. The user has
already told their proxy client which sites need it; frago's job is to
route the browser through that client, not to re-decide anything.

Which public sites take the proxy is not decided here. That belongs to
the proxy client, which ships rule sets covering tens of thousands of
domains and updates them on its own; any domain list frago kept would be
permanently behind, and being behind is expensive in both directions —
a missed domestic domain takes a slow detour abroad, a missed foreign
one does not load at all.

There is one class the proxy client cannot decide, because it cannot
know about it: addresses that are not on the public internet. The
machine itself, the local network, and an employer's internal hosts
match nothing in a public rule set, so they fall through to its
catch-all and get sent out through the exit node — where an internal
address simply does not exist. Those have to skip the proxy outright,
which is what the bypass list is for.

So this module answers two questions: *is there a local proxy, and on
which port*, and *what must never be sent to it*.

Detection is layered so an explicit answer always beats a guess:

1. ``FRAGO_BROWSER_PROXY`` — the deliberate override. A proxy URL, or
   ``off`` to launch with no proxy at all.
2. The standard proxy environment variables.
3. A scan of the ports the common proxy clients listen on.

A port that merely accepts a connection proves nothing — plenty of
unrelated services sit on 8080. Every candidate must complete an HTTP
``CONNECT`` before it is believed.
"""
from __future__ import annotations

import os
import platform
import socket
import subprocess
from urllib.parse import urlparse

# Ports the common desktop proxy clients listen on, most likely first.
# Clash/mihomo's mixed port is far and away the most common, so it is
# tried first and usually ends the scan in a millisecond.
_CANDIDATE_PORTS: tuple[int, ...] = (
    7890,   # Clash / mihomo / Clash Verge — mixed HTTP+SOCKS
    7891,   # Clash — HTTP-only port when split from the mixed one
    10809,  # v2rayN / Xray — HTTP
    6152,   # Surge — HTTP
    1087,   # ShadowsocksX-NG — HTTP
    8889,   # Quantumult X, some Shadowsocks builds
)

_PROXY_ENV_VARS: tuple[str, ...] = (
    "https_proxy", "HTTPS_PROXY",
    "http_proxy", "HTTP_PROXY",
    "all_proxy", "ALL_PROXY",
)

# Addresses that must never be handed to the proxy.
#
# A proxy client's rule set is written for the public internet. It has
# no way to know about the machine itself, the local network, or an
# employer's internal hosts, so anything in those categories falls
# through to the rule set's catch-all and is sent out through whatever
# exit node the user picked — which for an internal address means it
# simply does not resolve.
#
# ``<local>`` covers hostnames with no dot in them (``wiki``,
# ``build-server``), which is what an internal DNS suffix search
# produces. Loopback is left to Chrome's own implicit bypass — the
# ``<-loopback>`` directive that often appears in copied snippets
# *cancels* that bypass rather than adding it.
_BASE_BYPASS: tuple[str, ...] = (
    "<local>",
    "*.local",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "169.254.0.0/16",
)

# Corporate domains cannot be guessed, so they are taken from wherever
# the user has already written them down, in this order.
_BYPASS_ENV_VARS: tuple[str, ...] = (
    "FRAGO_BROWSER_PROXY_BYPASS",  # frago's own, wins by being first
    "no_proxy", "NO_PROXY",        # the cross-platform convention
)

_OFF_VALUES = frozenset({"off", "none", "0", "false", "no", ""})

# A CONNECT to this host is the proof a candidate is really an HTTP
# proxy. It never has to succeed end-to-end — the proxy answering "200"
# means it spoke the protocol, which is all we are asking.
_PROBE_HOST = "www.gstatic.com"
_PROBE_PORT = 443


def _normalize(value: str) -> str | None:
    """Turn a proxy setting into a URL Chrome accepts, or None."""
    value = value.strip()
    if not value or value.lower() in _OFF_VALUES:
        return None
    if "://" not in value:
        value = f"http://{value}"
    parsed = urlparse(value)
    if not parsed.hostname or not parsed.port:
        return None
    # SOCKS proxies are left alone — Chrome takes them verbatim.
    if parsed.scheme in ("socks5", "socks4", "socks"):
        return value
    return f"http://{parsed.hostname}:{parsed.port}"


def _speaks_http_proxy(host: str, port: int, timeout: float) -> bool:
    """True if something on host:port completes an HTTP CONNECT."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            request = (
                f"CONNECT {_PROBE_HOST}:{_PROBE_PORT} HTTP/1.1\r\n"
                f"Host: {_PROBE_HOST}:{_PROBE_PORT}\r\n\r\n"
            ).encode()
            sock.sendall(request)
            status_line = sock.recv(64)
    except OSError:
        return False
    # "HTTP/1.1 200 Connection established" — any 2xx counts. A real
    # proxy that refuses this particular host still identifies itself
    # by answering in HTTP, but we stay strict: a 2xx is unambiguous.
    return status_line.startswith(b"HTTP/") and b" 2" in status_line[:13]


def _system_bypass_entries() -> list[str]:
    """Whatever the OS already knows should skip the proxy.

    On macOS this is the exceptions list from Network settings, which on
    a managed laptop is usually where the employer's internal domains
    have already been written. Reading it means frago inherits that work
    instead of asking the user to repeat it.

    Silent on failure: a missing exceptions list is normal, and no
    browser should fail to launch over it.
    """
    if platform.system() != "Darwin":
        return []
    try:
        proc = subprocess.run(["scutil", "--proxy"], capture_output=True,
                              text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []

    entries: list[str] = []
    inside = False
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("ExceptionsList"):
            inside = True
            continue
        if inside:
            if stripped.startswith("}"):
                break
            # Lines look like "0 : 192.168.0.0/16"
            _, _, value = stripped.partition(":")
            value = value.strip()
            if value:
                entries.append(value)
    return entries


def proxy_bypass_list() -> str:
    """The ``--proxy-bypass-list`` value, in Chrome's semicolon format."""
    entries: list[str] = list(_BASE_BYPASS)

    for var in _BYPASS_ENV_VARS:
        raw = os.environ.get(var)
        if not raw:
            continue
        # no_proxy is comma-separated; frago's own var accepts either.
        entries.extend(part.strip()
                       for part in raw.replace(";", ",").split(",")
                       if part.strip())

    entries.extend(_system_bypass_entries())

    seen: set[str] = set()
    ordered: list[str] = []
    for entry in entries:
        if entry not in seen:
            seen.add(entry)
            ordered.append(entry)
    return ";".join(ordered)


def detect_local_proxy(*, timeout: float = 1.5) -> str | None:
    """Return the proxy URL the browser should use, or None for direct.

    Never raises: a browser that launches without a proxy is worse than
    one that launches with it, but far better than one that fails to
    launch because probing went wrong.
    """
    override = os.environ.get("FRAGO_BROWSER_PROXY")
    if override is not None:
        return _normalize(override)

    for var in _PROXY_ENV_VARS:
        raw = os.environ.get(var)
        if raw:
            normalized = _normalize(raw)
            if normalized:
                return normalized

    for port in _CANDIDATE_PORTS:
        if _speaks_http_proxy("127.0.0.1", port, timeout):
            return f"http://127.0.0.1:{port}"

    return None
