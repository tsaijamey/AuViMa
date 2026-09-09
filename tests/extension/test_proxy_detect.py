"""detect_local_proxy unit tests.

The point of these is that the browser must never be routed somewhere
the user did not ask for. So the cases that matter are the negative
ones: an explicit "off" is obeyed, and a port that answers but is not a
proxy is rejected rather than trusted.
"""
from __future__ import annotations

import socket
import threading

import pytest

from frago.browser import proxy_detect
from frago.browser.proxy_detect import detect_local_proxy

_ENV_VARS = ("FRAGO_BROWSER_PROXY", *proxy_detect._PROXY_ENV_VARS)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """No proxy env leaks in from the machine running the tests."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def no_ports(monkeypatch):
    """Nothing on any candidate port, so only env decides."""
    monkeypatch.setattr(proxy_detect, "_speaks_http_proxy",
                        lambda host, port, timeout: False)


def _serve_once(reply: bytes) -> tuple[int, threading.Thread]:
    """Listen on a free port, send ``reply`` to one client, then close."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def run():
        try:
            conn, _ = srv.accept()
            with conn:
                conn.recv(1024)
                conn.sendall(reply)
        except OSError:
            pass
        finally:
            srv.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return port, thread


# ── explicit override wins ──────────────────────────────────────────

def test_override_off_disables_proxy(monkeypatch):
    """`off` beats a live proxy — the user said no."""
    monkeypatch.setenv("FRAGO_BROWSER_PROXY", "off")
    monkeypatch.setattr(proxy_detect, "_speaks_http_proxy",
                        lambda host, port, timeout: True)
    assert detect_local_proxy() is None


def test_override_beats_env(monkeypatch, no_ports):
    monkeypatch.setenv("FRAGO_BROWSER_PROXY", "127.0.0.1:9999")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1111")
    assert detect_local_proxy() == "http://127.0.0.1:9999"


def test_bare_hostport_gains_scheme(monkeypatch, no_ports):
    monkeypatch.setenv("FRAGO_BROWSER_PROXY", "127.0.0.1:7890")
    assert detect_local_proxy() == "http://127.0.0.1:7890"


def test_socks_url_passed_through(monkeypatch, no_ports):
    monkeypatch.setenv("FRAGO_BROWSER_PROXY", "socks5://127.0.0.1:1080")
    assert detect_local_proxy() == "socks5://127.0.0.1:1080"


def test_malformed_override_falls_back_to_direct(monkeypatch, no_ports):
    """A port-less value is not a proxy; do not guess one."""
    monkeypatch.setenv("FRAGO_BROWSER_PROXY", "http://no-port-here")
    assert detect_local_proxy() is None


# ── environment variables ───────────────────────────────────────────

def test_env_var_used_when_no_override(monkeypatch, no_ports):
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:7890")
    assert detect_local_proxy() == "http://127.0.0.1:7890"


def test_https_proxy_preferred_over_all_proxy(monkeypatch, no_ports):
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1111")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:2222")
    assert detect_local_proxy() == "http://127.0.0.1:2222"


def test_empty_env_var_ignored(monkeypatch, no_ports):
    monkeypatch.setenv("HTTPS_PROXY", "")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:7890")
    assert detect_local_proxy() == "http://127.0.0.1:7890"


# ── port probing ────────────────────────────────────────────────────

def test_no_proxy_anywhere_means_direct(no_ports):
    assert detect_local_proxy() is None


def test_probe_accepts_a_real_connect_reply():
    port, _ = _serve_once(b"HTTP/1.1 200 Connection established\r\n\r\n")
    assert proxy_detect._speaks_http_proxy("127.0.0.1", port, 2.0) is True


def test_probe_rejects_a_listener_that_is_not_a_proxy():
    """The 8080-is-something-else case: answers, but not as a proxy."""
    port, _ = _serve_once(b"HTTP/1.1 404 Not Found\r\n\r\n")
    assert proxy_detect._speaks_http_proxy("127.0.0.1", port, 2.0) is False


def test_probe_rejects_a_silent_listener():
    """Accepts the connection, says nothing — must not be trusted."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        assert proxy_detect._speaks_http_proxy("127.0.0.1", port, 0.3) is False
    finally:
        srv.close()


def test_probe_rejects_a_closed_port():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.close()
    assert proxy_detect._speaks_http_proxy("127.0.0.1", port, 0.3) is False


def test_first_answering_candidate_port_wins(monkeypatch):
    """Scan order is priority order, and it stops at the first hit."""
    seen: list[int] = []

    def fake(host, port, timeout):
        seen.append(port)
        return port == proxy_detect._CANDIDATE_PORTS[1]

    monkeypatch.setattr(proxy_detect, "_speaks_http_proxy", fake)
    expected = proxy_detect._CANDIDATE_PORTS[1]
    assert detect_local_proxy() == f"http://127.0.0.1:{expected}"
    assert seen == list(proxy_detect._CANDIDATE_PORTS[:2])


# ── bypass list ─────────────────────────────────────────────────────

@pytest.fixture
def no_system_bypass(monkeypatch):
    """Ignore whatever the test machine has in Network settings."""
    monkeypatch.setattr(proxy_detect, "_system_bypass_entries", list)


def test_private_ranges_always_bypass(no_system_bypass):
    """An internal address must never be handed to an exit node."""
    entries = proxy_detect.proxy_bypass_list().split(";")
    for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"):
        assert cidr in entries


def test_dotless_hostnames_bypass(no_system_bypass):
    """`<local>` covers intranet names resolved by DNS suffix search."""
    assert "<local>" in proxy_detect.proxy_bypass_list().split(";")


def test_loopback_bypass_is_not_cancelled(no_system_bypass):
    """`<-loopback>` would *disable* Chrome's implicit loopback bypass."""
    assert "<-loopback>" not in proxy_detect.proxy_bypass_list()


def test_corporate_domain_can_be_added(monkeypatch, no_system_bypass):
    monkeypatch.setenv("FRAGO_BROWSER_PROXY_BYPASS", "*.lenovo.com,*.corp")
    entries = proxy_detect.proxy_bypass_list().split(";")
    assert "*.lenovo.com" in entries
    assert "*.corp" in entries


def test_no_proxy_env_is_honoured(monkeypatch, no_system_bypass):
    monkeypatch.setenv("no_proxy", "internal.example.com, 10.1.2.3")
    entries = proxy_detect.proxy_bypass_list().split(";")
    assert "internal.example.com" in entries
    assert "10.1.2.3" in entries


def test_system_exceptions_are_inherited(monkeypatch):
    """The OS exceptions list is where corporate domains usually live."""
    monkeypatch.setattr(proxy_detect, "_system_bypass_entries",
                        lambda: ["*.intranet.example", "192.168.0.0/16"])
    entries = proxy_detect.proxy_bypass_list().split(";")
    assert "*.intranet.example" in entries
    assert entries.count("192.168.0.0/16") == 1, "duplicates must collapse"


def test_bypass_list_never_empty(no_system_bypass):
    assert proxy_detect.proxy_bypass_list().strip()
