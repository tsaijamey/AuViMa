#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 控制页面滚动
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      提供页面滚动控制功能，支持向上、向下、顶部、底部等方向滚动
# 用法: ./cdp_scroll.sh [up|down|top|bottom|<pixels>]
# 标准化: 使用websocat和CDP的Input.dispatchMouseEvent(wheel)

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 参数处理
DIRECTION="${1:-down}"

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

# 处理滚动参数
case "$DIRECTION" in
    up)
        DELTA_Y="-300"
        MSG="向上滚动"
        ;;
    down)
        DELTA_Y="300"
        MSG="向下滚动"
        ;;
    top)
        # 滚动到顶部使用JavaScript
        JS_CODE="window.scrollTo({top: 0, behavior: 'smooth'}); 'scrolled to top'"
        ;;
    bottom)
        # 滚动到底部使用JavaScript
        JS_CODE="window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'smooth'}); 'scrolled to bottom'"
        ;;
    [0-9]*)
        # 数字表示向下滚动的像素数
        DELTA_Y="$DIRECTION"
        MSG="向下滚动 ${DIRECTION}px"
        ;;
    -[0-9]*)
        # 负数表示向上滚动
        DELTA_Y="$DIRECTION"
        MSG="向上滚动 ${DIRECTION#-}px"
        ;;
    *)
        error_log "无效的滚动参数: $DIRECTION"
        echo "用法: $0 [up|down|top|bottom|<pixels>]"
        echo "例如: $0 down      # 向下滚动300px"
        echo "      $0 up        # 向上滚动300px"
        echo "      $0 500       # 向下滚动500px"
        echo "      $0 -500      # 向上滚动500px"
        echo "      $0 top       # 滚动到顶部"
        echo "      $0 bottom    # 滚动到底部"
        exit 2
        ;;
esac

# 如果是使用JavaScript的特殊滚动（top/bottom）
if [ -n "${JS_CODE:-}" ]; then
    debug_log "使用JavaScript滚动: $DIRECTION"
    
    # 转义JavaScript代码
    JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')
    
    # 构建CDP命令
    SCROLL_CMD=$(cat <<EOF
{
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "$JS_ESCAPED",
        "returnByValue": true
    }
}
EOF
    )
    
    # 使用execute_cdp_command发送命令
    RESPONSE=$(execute_cdp_command "Runtime.evaluate" "{\"expression\":\"$JS_CODE\",\"returnByValue\":true}") || {
        error_log "滚动失败"
        exit 1
    }
    
    success_log "$DIRECTION"
else
    # 使用Input.dispatchMouseEvent进行滚动
    debug_log "$MSG"
    
    # 获取视口中心点（滚轮事件需要坐标）
    GET_VIEWPORT_JS="
    ({
        x: window.innerWidth / 2,
        y: window.innerHeight / 2
    })
    "
    
    # 使用execute_cdp_command获取视口中心坐标
    VIEWPORT_RESPONSE=$(execute_cdp_command "Runtime.evaluate" "{\"expression\":\"$GET_VIEWPORT_JS\",\"returnByValue\":true}") || {
        error_log "无法获取视口信息"
        exit 1
    }
    
    # 提取坐标
    X=$(echo "$VIEWPORT_RESPONSE" | sed -n 's/.*"x":\([0-9.]*\).*/\1/p' | head -1)
    Y=$(echo "$VIEWPORT_RESPONSE" | sed -n 's/.*"y":\([0-9.]*\).*/\1/p' | head -1)
    
    if [ -z "$X" ] || [ -z "$Y" ]; then
        # 使用默认值
        X="400"
        Y="300"
        debug_log "使用默认坐标: x=$X, y=$Y"
    else
        debug_log "视口中心: x=$X, y=$Y"
    fi
    
    # 发送滚轮事件
    WHEEL_CMD=$(cat <<EOF
{
    "id": 2,
    "method": "Input.dispatchMouseEvent",
    "params": {
        "type": "mouseWheel",
        "x": $X,
        "y": $Y,
        "deltaX": 0,
        "deltaY": $DELTA_Y,
        "modifiers": 0
    }
}
EOF
    )
    
    debug_log "发送滚轮事件: deltaY=$DELTA_Y"
    
    # 使用execute_cdp_command发送滚轮事件
    WHEEL_PARAMS="{\"type\":\"mouseWheel\",\"x\":${X:-400},\"y\":${Y:-300},\"deltaX\":0,\"deltaY\":$DELTA_Y}"
    RESPONSE=$(execute_cdp_command "Input.dispatchMouseEvent" "$WHEEL_PARAMS") || {
        error_log "滚动失败"
        exit 1
    }
    
    # 获取当前滚动位置（用于验证）
    GET_POS_JS="({x: window.pageXOffset, y: window.pageYOffset})"
    
    # 使用execute_cdp_command获取滚动位置
    POS_RESPONSE=$(execute_cdp_command "Runtime.evaluate" "{\"expression\":\"$GET_POS_JS\",\"returnByValue\":true}") || {
        debug_log "无法获取滚动位置"
    }
    
    if [ -n "$POS_RESPONSE" ]; then
        SCROLL_Y=$(echo "$POS_RESPONSE" | sed -n 's/.*"y":\([0-9.]*\).*/\1/p' | head -1)
        [ -n "$SCROLL_Y" ] && debug_log "当前滚动位置: y=$SCROLL_Y"
    fi
    
    success_log "$MSG"
fi