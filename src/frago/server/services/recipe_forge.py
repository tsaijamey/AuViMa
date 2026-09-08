"""在图形界面里创建配方 —— 起一个「导演」会话，让人在虚拟桌面上看着配方被做出来。

## 控制链（一共四段，展示层与控制层分开）

    配方管理页「创建配方」→ 需求 + 要不要界面
        ↓  本模块：写一份导演任务书，起一场隐藏的 claude 会话，任务书是第一句话
    导演（隐藏 tmux 里的 claude，人看不见它）
        ↓  用 ``frago desktop`` 指挥桌面；用 ``frago recipe create --tmux-target frago-stage``
           让 worker 跑在桌面终端里
    虚拟桌面（人看的显示器）：终端窗口里 worker 在写配方，浏览器窗口里配方页面在长
        ↑  桌面页带 ``?userInput=true&session=<导演会话>`` 时露出一条输入行，
           人打的字**不进桌面终端**，而是排进导演的队列，由导演转达给 worker

桌面只是显示器；导演是遥控器；人对着遥控器说话。本模块只负责把遥控器造出来并
递给页面，之后的一切都由导演按任务书自己走。

分层：服务层。可以 import ``desktop/``、``session/`` 与同层服务，NEVER import ``cli/``。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from frago.server.services import workbench_agents, workbench_new_session

logger = logging.getLogger(__name__)

#: 虚拟桌面终端窗口盯着的 tmux 会话。worker 借住在这里跑，人才看得见它。
STAGE_TMUX_SESSION = "frago-stage"

#: 导演会话的工作目录。配方落在 ``~/.frago/recipes`` 下，与工作目录无关；选家目录
#: 只是让 worker 的记录文件落到一个稳定、不属于任何仓库的地方。
_DIRECTOR_CWD = Path.home()

#: 配方名的合法形状，与目录名、recipe.md 的 name、类名三处一致的那一个。
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class DesktopNotRunning(RuntimeError):
    """虚拟桌面没在跑。导演的第一条铁律就是不许自己拉起它，所以这里先拦下。"""


class BadRecipeName(ValueError):
    """配方名不是 snake_case，或者已经有同名配方。"""


@dataclass(frozen=True)
class ForgeLaunch:
    """一次「创建配方」起好之后，页面要拿去的东西。"""

    session_id: str
    """导演会话的编号——桌面输入行往这里投话。"""

    desktop_url: str
    """带 userInput 开关与会话编号的桌面地址，页面用它开那扇「APP 模式」窗口。"""

    recipe_name: str | None
    """人指定的配方名；没指定就是 None，由导演定名。"""


def desktop_page_url(session_id: str) -> str:
    """桌面页的地址：相对路径，页面自己知道自己挂在哪个主机上。"""
    return f"/app/agent_os?userInput=true&session={session_id}"


def _ensure_desktop_running() -> None:
    from frago.desktop import registry

    record = registry.read_instance()
    if record is None or record.get("status") != "running":
        raise DesktopNotRunning(
            "虚拟桌面没在跑。先执行 frago desktop up，再回来创建配方——导演会话不会替你拉起它。"
        )


def _check_name(name: str | None) -> str | None:
    if name is None or not name.strip():
        return None
    name = name.strip()
    if not _NAME_RE.match(name):
        raise BadRecipeName(
            f"配方名 {name!r} 不合法：只能是小写字母、数字、下划线，以字母开头（snake_case）"
        )
    try:
        from frago.recipes.registry import get_registry

        get_registry().find(name)
    except Exception:
        return name  # 找不到才是想要的结果
    raise BadRecipeName(f"已经有一个叫 {name!r} 的配方了，换一个名字")


def build_brief(requirement: str, *, page: bool, name: str | None, session_id: str) -> str:
    """写给导演的任务书。

    导演是一场普通的 claude 会话，它对这条控制链一无所知；它知道的一切都在这份任务
    书里。所以任务书写的是**它能直接敲的命令**和**它必须守的边界**，不是设计说明。
    """
    ui_line = "需要界面：是。" if page else (
        "需要界面：否。写需求文件时在末尾加一行「page: false，不要页面」，"
        "规格里任何 mode 都不能标 action。"
    )
    name_line = (
        f"配方名：{name}（人指定的，照用）。"
        if name
        else "配方名：由你定。英文 snake_case，一眼看得出它干什么。"
    )
    forge_dir = f"~/.frago/forge/{session_id}"
    return f"""你是「配方开发导演」。一个人正在浏览器里看着虚拟桌面（frago desktop）；你不在画面里。
你的工作是指挥：让 worker 在桌面终端里把配方写出来，让桌面浏览器展示配方页面的演进，
把人中途追加的需求转达给 worker。人只看桌面，不看你这里的文字。

## 需求（原话，一个字都不要改）

{requirement.strip()}

{ui_line}
{name_line}

## 铁律

1. 虚拟桌面必须一直活着。NEVER 执行 frago desktop down、frago desktop up、frago server restart、
   frago browser -b cdp start、tmux kill-session。桌面不在跑就停下来在本会话里汇报，不要自己拉。
2. worker 必须跑在桌面终端里，人才看得见：只用
   frago recipe create <名字> --prompt-file <需求文件> --tmux-target {STAGE_TMUX_SESSION}
   NEVER 用不带 --tmux-target 的 plan/create；NEVER 自己在桌面终端里手敲 claude。
3. plan/create 是阻塞命令、不设时间上限，MUST 用 Bash 工具 run_in_background: true 起；跑完 harness
   会通知你。NEVER 从外面套 timeout 或 kill。
4. 说话只用 frago desktop say "<一句话>"（30 字以内），在每个里程碑说一句：定名、开始写规格、
   开始写代码、页面出来了、验证通过、完成 / 失败。NEVER 向人解释代码或过程细节。
5. 人追加的需求会作为**新消息**到达本会话。收到后立刻：
   a. frago desktop say "收到，已转达：<不超过 20 字的摘要>"
   b. worker 还在跑（后台 create 命令没结束）时，把原话排进 worker 的队列：
      frago desktop focus term
      frago desktop type "<原话>"
      sleep 2
      frago desktop key Enter
   c. worker 已经结束时，把原话追加进需求文件末尾，再按第 2 条重新起一轮
      frago recipe create <名字> --force --prompt-file <需求文件> --tmux-target {STAGE_TMUX_SESSION}
6. 需要人处理（create 退出码 2：认证墙 / 澄清菜单）时，frago desktop say "需要你处理：<原因>"，
   并在本会话里写清楚卡在哪。

## 步骤

1. frago desktop status —— 确认 runtime.status 是 running。回执里的 WARN 逐条按要求书面回应。
2. 定名：frago recipe list --format names 查重；定下后 frago desktop say "配方名：<名字>"。
3. mkdir -p {forge_dir}，把「需求」那一段原样写进 {forge_dir}/requirement.md（含「需要界面」那一行）。
4. 桌面布局：frago desktop term fontsize 18。不需要界面时再执行
   frago desktop window close --target browser 与 frago desktop window max --target term。
5. 后台起（run_in_background: true）：
   frago recipe create <名字> --prompt-file {forge_dir}/requirement.md --tmux-target {STAGE_TMUX_SESSION}
6. 需要界面时，另起一个后台 bash 循环（同样 run_in_background: true），内容是：
   每 5 秒查一次 ~/.frago/recipes 下 <名字>/assets/index.html 是否出现；出现后执行
   frago desktop browser open http://127.0.0.1:8093/app/<名字>/ 并 say "页面出来了"；
   此后每 20 秒比较 assets 目录内文件的最新修改时间，变了就再 open 一次同一地址（等于刷新）；
   直到第 5 步的命令结束后再刷最后一次。
7. create 结束：
   - 退出码 0 → frago recipe validate <配方目录>；再 frago recipe run <名字>（有页面就会有状态）；
     需要界面时再 open 一次页面；say "配方完成，可以在配方页启动"。
   - 退出码 2 → 按铁律第 6 条。
   - 其它 → say "失败：<一句原因>"，并在本会话里写明。
8. 最后在本会话里给一份 5 行以内的总结：配方名、目录、modes、下一步。之后继续留在本会话里等人
   追加需求（铁律第 5 条）。
"""


def start(requirement: str, *, page: bool = True, name: str | None = None) -> ForgeLaunch:
    """起一场导演会话并投进任务书，立刻返回页面要开的桌面地址。

    先查两件事再动：桌面在不在跑、名字合不合法。两件都是当场能答的，NEVER 起了会话
    再让导演去发现——那时页面已经跳进桌面，人对着一块什么都不会发生的屏幕干等。
    """
    if not requirement.strip():
        raise ValueError("需求不能是空的")
    _ensure_desktop_running()
    checked_name = _check_name(name)

    agent = workbench_agents.require_selectable("claude")
    # 任务书里要写导演自己的会话编号（需求文件落在以它命名的目录下），而第一句话是
    # 起会话那一刻投进去的——所以编号在这里先定好，会话与任务书用同一个。
    import uuid

    session_id = str(uuid.uuid4())
    brief = build_brief(requirement, page=page, name=checked_name, session_id=session_id)
    launch = workbench_new_session.start_with_id(
        agent.agent_type, str(_DIRECTOR_CWD), brief, session_id=session_id
    )
    logger.info("recipe forge: director session=%s page=%s name=%s", launch.session_id, page, name)
    return ForgeLaunch(
        session_id=launch.session_id or session_id,
        desktop_url=desktop_page_url(launch.session_id or session_id),
        recipe_name=checked_name,
    )
