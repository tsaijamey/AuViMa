#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 获取页面标题
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      获取当前页面的标题，用于页面识别和验证
# 用法: ./cdp_get_title.sh
# 标准化: 使用websocat和CDP的Runtime.evaluate

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 检查CDP环境
check_cdp_environment || exit $?

debug_log "获取页面标题..."

# 使用execute_cdp_command函数
PARAMS='{"expression":"document.title","returnByValue":true}'
RESPONSE=$(execute_cdp_command "Runtime.evaluate" "$PARAMS") || {
    error_log "无法获取页面标题"
    exit 1
}

# 提取标题
if echo "$RESPONSE" | grep -q '"result"'; then
    TITLE=$(parse_json "$RESPONSE" '.result.result.value' 2>/dev/null || echo "")
    
    if [ -z "$TITLE" ] || [ "$TITLE" = "null" ]; then
        # 尝试其他路径
        TITLE=$(parse_json "$RESPONSE" '.result.value' 2>/dev/null || echo "")
    fi
    
    if [ -n "$TITLE" ] && [ "$TITLE" != "null" ]; then
        echo "$TITLE"
        debug_log "页面标题: $TITLE"
    else
        info_log "页面无标题"
    fi
else
    error_log "无效的响应格式"
    exit 1
fi