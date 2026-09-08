"""System status and info API endpoints.

Provides endpoints for server health checks and information.
"""

from fastapi import APIRouter

from frago.server.models import (
    ClaudeUsageResponse,
    ServerInfoResponse,
    SystemDirectoriesResponse,
    SystemStatusResponse,
)
from frago.server.services.system_service import SystemService
from frago.server.utils import get_server_info

router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
async def get_status() -> SystemStatusResponse:
    """Get system status.

    Returns information about Chrome availability,
    running tasks, and monitored projects.
    """
    status = SystemService.get_status()

    return SystemStatusResponse(
        cpu_percent=status.get("cpu_percent", 0.0),
        memory_percent=status.get("memory_percent", 0.0),
        browser_available=status.get("browser_available", False),
        browser_connected=status.get("browser_connected", False),
        projects_count=status.get("projects_count", 0),
        tasks_running=status.get("tasks_running", 0),
        tab_count=status.get("tab_count", 0),
    )


@router.get("/info", response_model=ServerInfoResponse)
async def get_info() -> ServerInfoResponse:
    """Get server information.

    Returns server version, host, port, and start time.
    """
    from datetime import datetime

    server_info = get_server_info()

    info = SystemService.get_info(
        host=server_info.get("host", "127.0.0.1"),
        port=server_info.get("port", 8080),
        started_at=server_info.get("started_at", datetime.now().isoformat()),
    )

    return ServerInfoResponse(
        version=info.get("version", "0.0.0"),
        host=info.get("host", "127.0.0.1"),
        port=info.get("port", 8080),
        started_at=datetime.fromisoformat(info.get("started_at", datetime.now().isoformat())),
    )


@router.get("/system/directories", response_model=SystemDirectoriesResponse)
async def get_directories() -> SystemDirectoriesResponse:
    """Get system default directories.

    Returns user home directory and current working directory.
    Used as fallback when no recent directories exist.
    """
    dirs = SystemService.get_directories()

    return SystemDirectoriesResponse(
        home=dirs.get("home", ""),
        cwd=dirs.get("cwd"),
    )


@router.get("/system/claude-usage", response_model=ClaudeUsageResponse)
async def get_claude_usage(refresh: bool = False) -> ClaudeUsageResponse:
    """本机 Claude Code 的订阅额度。

    读的是后台每十分钟探一次的缓存，不在请求路径上跑 claude——那要三秒钟，界面第一次
    画出来的时间不该押在它身上。`refresh=true` 才当场重探。
    """
    from frago.server.services.claude_usage_service import ClaudeUsageService

    service = ClaudeUsageService.get_instance()
    usage = await service.refresh() if refresh else service.get_usage()

    return ClaudeUsageResponse(**usage)
