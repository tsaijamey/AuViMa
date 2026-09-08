"""Claude Code 订阅额度的定期探测。

**这件事只有本机答得出来。** 订阅额度不在 frago 的任何一张表里，也没有公开接口可查；
唯一能说出「这周用掉多少」的是装在这台机器上的 Claude Code 自己，问法是
`claude -p "/usage"`。所以这一项能力天然绑定本机：机器上没有 claude 就没有这个数，
界面上那三根条子就整个不出现，而不是画三根空的。

**探测走安全模式，这不是可选项。** 直接跑 `claude -p "/usage"` 会付三笔与用量无关的
代价：触发一整套 hook（其中有要花钱的 LightAgent 判读）、在 ~/.claude/projects 下留一份
会话记录（十分钟一份，一天一百四十四份，会话页会被这些探测记录淹掉）、以及多花一倍
时间加载插件与 CLAUDE.md。`--safe-mode` 关掉全部定制、`--no-session-persistence`
不落盘，登录态照常读得到——这两个开关加在一起，探测才是干净的。

**十分钟一次是按额度自己的变化速度定的。** 三档里跑得最快的是五小时会话窗口，一次
问答改变不了它一个百分点；再密只是重复问同一个答案。
"""

import asyncio
import contextlib
import logging
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 探测间隔（秒）。十分钟——见模块开头。
USAGE_CHECK_INTERVAL_SECONDS = 600

# 单次探测的上限。实测约 3 秒；给到 60 秒是为了让一台正在换 token 或网络很慢的机器
# 也有机会答完，而不是每一轮都被自己掐死。
USAGE_PROBE_TIMEOUT_SECONDS = 60

PROBE_ARGV = ["--safe-mode", "--no-session-persistence", "-p", "/usage"]

# `/usage` 的三行。百分比后面那截「resets ...」照原样留着当 tooltip，不解析成时间——
# 它带着人自己的时区名，重新格式化只会把这条信息弄丢。
_SESSION_RE = re.compile(r"^Current session:\s*(\d+)%\s*used(?:\s*·\s*resets\s*(.+?))?\s*$")
_WEEK_ALL_RE = re.compile(
    r"^Current week \(all models\):\s*(\d+)%\s*used(?:\s*·\s*resets\s*(.+?))?\s*$"
)
_WEEK_MODEL_RE = re.compile(
    r"^Current week \((?!all models\))([^)]+)\):\s*(\d+)%\s*used(?:\s*·\s*resets\s*(.+?))?\s*$"
)


def _empty_usage(reason: str | None = None) -> dict[str, Any]:
    """没有数可报时的那份形状。界面靠 `available` 决定画不画，不靠猜字段有没有。"""
    return {
        "available": False,
        "session": None,
        "week_all": None,
        "week_model": None,
        "checked_at": None,
        "error": reason,
    }


class ClaudeUsageService:
    """定期问本机 Claude Code 要订阅额度，缓存并推给界面。"""

    _instance: Optional["ClaudeUsageService"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._cache: dict[str, Any] = _empty_usage()
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    @classmethod
    def get_instance(cls) -> "ClaudeUsageService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        """起后台探测循环。机器上没装 claude 也照起——装上之后不必重启服务。"""
        if self._task is not None and not self._task.done():
            logger.warning("Claude usage service already running")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._check_loop())
        logger.info(
            "Claude usage service started (interval: %ss)", USAGE_CHECK_INTERVAL_SECONDS
        )

    async def stop(self) -> None:
        if self._task is None or self._task.done():
            return

        self._stop_event.set()
        self._task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self._task

        self._task = None
        logger.info("Claude usage service stopped")

    async def _check_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._do_check()
            except Exception as e:
                logger.warning("Claude usage probe failed: %s", e)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=USAGE_CHECK_INTERVAL_SECONDS
                )
                break
            except TimeoutError:
                continue

    async def _do_check(self) -> None:
        """跑一次探测；只有数变了才广播——不变的数推给界面没有意义。"""
        loop = asyncio.get_event_loop()
        usage = await loop.run_in_executor(None, self._probe)

        if usage != self._cache:
            self._cache = usage
            await self._broadcast()

    def _probe(self) -> dict[str, Any]:
        """在线程池里跑 claude，把它说的话解析成三档百分比。"""
        binary = shutil.which("claude")
        if not binary:
            return _empty_usage("claude-not-installed")

        try:
            result = subprocess.run(
                [binary, *PROBE_ARGV],
                capture_output=True,
                text=True,
                timeout=USAGE_PROBE_TIMEOUT_SECONDS,
                # 探测跟仓库无关，放在家目录跑：省掉进入某个项目时的信任提示与目录扫描。
                cwd=os.path.expanduser("~"),
            )
        except subprocess.TimeoutExpired:
            return _empty_usage("probe-timeout")
        except OSError as e:
            return _empty_usage(f"probe-failed: {e}")

        if result.returncode != 0:
            detail = (result.stderr or "").strip().splitlines()
            return _empty_usage(f"probe-exit-{result.returncode}: {detail[0] if detail else ''}")

        return self._parse(result.stdout or "")

    @staticmethod
    def _parse(output: str) -> dict[str, Any]:
        """把 `/usage` 的输出读成三档。

        用 API key 而不是订阅的人，这条命令根本不报百分比——那种机器上没有「额度」这回事，
        返回不可用，界面上就没有这三根条子。
        """
        usage = _empty_usage()

        for raw in output.splitlines():
            line = raw.strip()

            m = _SESSION_RE.match(line)
            if m:
                usage["session"] = {"percent": int(m.group(1)), "resets_at": m.group(2)}
                continue

            m = _WEEK_ALL_RE.match(line)
            if m:
                usage["week_all"] = {"percent": int(m.group(1)), "resets_at": m.group(2)}
                continue

            # 型号那一档的名字跟着账号走（Fable / Opus / …），写死一个就只对一种账号成立。
            m = _WEEK_MODEL_RE.match(line)
            if m:
                usage["week_model"] = {
                    "label": m.group(1).strip(),
                    "percent": int(m.group(2)),
                    "resets_at": m.group(3),
                }

        usage["checked_at"] = datetime.now().isoformat()

        if usage["session"] or usage["week_all"] or usage["week_model"]:
            usage["available"] = True
            usage["error"] = None
        else:
            usage["error"] = "no-subscription-usage"

        return usage

    async def _broadcast(self) -> None:
        try:
            from frago.server.websocket import create_message, manager

            message = create_message("data_claude_usage", {"data": self._cache})
            await manager.broadcast(message)
        except Exception as e:
            logger.warning("Failed to broadcast Claude usage: %s", e)

    def get_usage(self) -> dict[str, Any]:
        """界面第一次打开时读缓存。首轮探测还没回来就先给一份「暂时没有」。"""
        return self._cache

    async def refresh(self) -> dict[str, Any]:
        """立刻探测一次，不等下一个十分钟。"""
        await self._do_check()
        return self._cache
