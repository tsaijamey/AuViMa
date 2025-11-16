"""
CDP类型定义

定义Chrome DevTools Protocol相关的类型提示。
"""

from typing import Dict, Any, Optional, Union, List, TypedDict


# CDP命令相关类型
CommandParams = Dict[str, Any]
CommandResult = Dict[str, Any]


class CDPResponse(TypedDict, total=False):
    """CDP响应数据结构"""
    id: int
    result: Optional[CommandResult]
    error: Optional[Dict[str, Any]]
    method: Optional[str]
    params: Optional[Dict[str, Any]]


class CDPRequest(TypedDict):
    """CDP请求数据结构"""
    id: int
    method: str
    params: Optional[CommandParams]


# 连接相关类型
WebSocketMessage = Union[str, bytes]


# 重试相关类型
RetryCallback = Any  # 重试回调函数类型


# 配置相关类型
ConfigDict = Dict[str, Any]


# 事件相关类型
EventHandler = Any  # 事件处理函数类型


class SessionInfo(TypedDict):
    """会话信息"""
    id: str
    title: str
    url: str
    type: str
    webSocketDebuggerUrl: str