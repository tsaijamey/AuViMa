"""在图形界面里创建配方：导演会话的起法与任务书的硬约束。

任务书是导演唯一知道的东西，所以这里钉的是它**必须写着**的那几句：worker 借住桌面
终端（--tmux-target frago-stage）、桌面不许停、人追加的话怎么转达、没界面时 page 为假。
起会话之前的两道闸（桌面在不在跑、名字合不合法）也在这里。
"""

from __future__ import annotations

import pytest

from frago.server.services import recipe_forge


def test_brief_pins_the_control_chain() -> None:
    brief = recipe_forge.build_brief(
        "每天抓一遍 ETF 净值画成走势图", page=True, name=None, session_id="sid-1"
    )
    assert "--tmux-target frago-stage" in brief
    assert "frago desktop down" in brief  # 铁律里点名禁止
    assert "run_in_background" in brief
    assert "frago desktop type" in brief and "frago desktop key Enter" in brief
    assert "~/.frago/forge/sid-1" in brief
    assert "由你定" in brief
    assert "browser open http://127.0.0.1:8093/app/<名字>/" in brief


def test_brief_without_page_asks_for_a_data_only_recipe() -> None:
    brief = recipe_forge.build_brief("x", page=False, name="etf_board", session_id="s")
    assert "page: false" in brief
    assert "window close --target browser" in brief
    assert "配方名：etf_board" in brief


def test_start_refuses_when_desktop_is_not_running(monkeypatch) -> None:
    from frago.desktop import registry

    monkeypatch.setattr(registry, "read_instance", lambda *_a, **_k: {"status": "stopped"})
    with pytest.raises(recipe_forge.DesktopNotRunning):
        recipe_forge.start("x")


def test_start_refuses_a_bad_name(monkeypatch) -> None:
    from frago.desktop import registry

    monkeypatch.setattr(registry, "read_instance", lambda *_a, **_k: {"status": "running"})
    with pytest.raises(recipe_forge.BadRecipeName):
        recipe_forge.start("x", name="Not Snake")


def test_start_refuses_an_existing_name(monkeypatch) -> None:
    from frago.desktop import registry
    from frago.recipes import registry as recipe_registry

    monkeypatch.setattr(registry, "read_instance", lambda *_a, **_k: {"status": "running"})

    class _Reg:
        def find(self, name):
            return object()

    monkeypatch.setattr(recipe_registry, "get_registry", lambda: _Reg())
    with pytest.raises(recipe_forge.BadRecipeName):
        recipe_forge.start("x", name="taken_name")


def test_start_hands_the_brief_to_a_claude_session_with_a_known_id(monkeypatch) -> None:
    from frago.desktop import registry
    from frago.server.services import workbench_agents, workbench_new_session

    monkeypatch.setattr(registry, "read_instance", lambda *_a, **_k: {"status": "running"})

    class _Agent:
        agent_type = "claude"
        id_origin = "caller"

    monkeypatch.setattr(workbench_agents, "require_selectable", lambda _t: _Agent())
    seen: dict = {}

    def fake_start_with_id(agent_type, cwd, prompt, *, session_id):
        seen.update(agent_type=agent_type, cwd=cwd, prompt=prompt, session_id=session_id)
        return workbench_new_session.PendingLaunch(
            handle=session_id, agent_type=agent_type, display_name="Claude Code",
            cwd=cwd, session_id=session_id,
        )

    monkeypatch.setattr(workbench_new_session, "start_with_id", fake_start_with_id)
    launch = recipe_forge.start("做一个看板", page=True)
    assert seen["agent_type"] == "claude"
    assert seen["session_id"] == launch.session_id
    # 任务书里写的目录用的正是这场会话的编号。
    assert f"~/.frago/forge/{launch.session_id}" in seen["prompt"]
    assert launch.desktop_url == f"/app/agent_os?userInput=true&session={launch.session_id}"
    assert launch.recipe_name is None


def test_send_queued_returns_before_the_turn_ends(monkeypatch) -> None:
    """排队投喂：判完落点就返回；真正的投喂在别的线程里，本线程不等。"""
    import threading

    from frago.server.services import session_send, ui_session_runner

    monkeypatch.setattr(
        session_send,
        "resolve_target",
        lambda sid, cwd_hint=None: session_send.SendTarget(
            sid, "claude-code", "claude", "/tmp", is_new=False
        ),
    )
    started = threading.Event()
    release = threading.Event()

    class _Runner:
        def send(self, *_a, **_k):
            started.set()
            release.wait(timeout=5)

    monkeypatch.setattr(ui_session_runner, "get_runner", lambda: _Runner())
    name = session_send.send_queued("abc", "补一句")
    assert name.startswith("webui-queued-send-")
    assert started.wait(timeout=2)  # 投喂确实开始了
    release.set()
