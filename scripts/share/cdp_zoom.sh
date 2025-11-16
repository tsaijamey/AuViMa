#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 控制页面缩放
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      调整页面缩放级别，用于响应式设计测试和视觉效果控制
# 用法: ./cdp_zoom.sh [zoom_level]
# 参数: zoom_level - 缩放级别（0.5-3.0），1.0为正常大小
# 标准化: 使用websocat和CDP的Emulation.setPageScaleFactor

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 参数处理
ZOOM_LEVEL="${1:-1.0}"

# 参数验证
if [ -z "$ZOOM_LEVEL" ]; then
    ZOOM_LEVEL="1.0"
fi

# 验证缩放级别是否为有效数字
if ! echo "$ZOOM_LEVEL" | grep -qE '^[0-9]+(\.[0-9]+)?$'; then
    error_log "无效的缩放级别: $ZOOM_LEVEL"
    echo "用法: $0 [zoom_level]"
    echo "zoom_level: 0.5-3.0之间的数字，1.0为正常大小"
    echo "例如: $0 1.5    # 放大到150%"
    echo "      $0 0.75   # 缩小到75%"
    echo "      $0 2      # 放大到200%"
    exit 2
fi

# 验证缩放范围（CDP支持0.1-5.0，但实际使用限制在0.5-3.0更合理）
if (( $(echo "$ZOOM_LEVEL < 0.5" | bc -l 2>/dev/null || echo "1") )) || \
   (( $(echo "$ZOOM_LEVEL > 3.0" | bc -l 2>/dev/null || echo "0") )); then
    error_log "缩放级别超出范围: $ZOOM_LEVEL"
    echo "缩放级别应在0.5到3.0之间"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

# 计算缩放百分比（用于显示）
ZOOM_PERCENT=$(echo "$ZOOM_LEVEL * 100" | bc -l 2>/dev/null || echo "${ZOOM_LEVEL}00")
ZOOM_PERCENT=${ZOOM_PERCENT%.*}  # 移除小数点

debug_log "设置缩放级别: ${ZOOM_PERCENT}%"

# 首先启用页面缩放功能
ENABLE_CMD=$(cat <<EOF
{
    "id": 1,
    "method": "Emulation.setDeviceMetricsOverride",
    "params": {
        "width": 0,
        "height": 0,
        "deviceScaleFactor": 0,
        "mobile": false
    }
}
EOF
)

# 发送启用命令（这会清除任何现有的设备仿真）
echo "$ENABLE_CMD" | websocat -t -n1 "$WS_URL" >/dev/null 2>&1

# 设置页面缩放级别
ZOOM_CMD=$(cat <<EOF
{
    "id": 2,
    "method": "Emulation.setPageScaleFactor",
    "params": {
        "pageScaleFactor": $ZOOM_LEVEL
    }
}
EOF
)

debug_log "发送缩放命令..."

# 发送缩放命令
RESPONSE=$(echo "$ZOOM_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "设置缩放级别失败"
    exit 1
}

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    
    # 如果是方法未找到错误，尝试使用替代方法
    if echo "$ERROR_MSG" | grep -q "not found"; then
        debug_log "尝试使用JavaScript设置缩放..."
        
        # 使用CSS zoom作为备用方案
        ZOOM_JS="document.body.style.zoom = '$ZOOM_LEVEL'; 'Zoom set to ${ZOOM_PERCENT}%'"
        JS_ESCAPED=$(printf '%s' "$ZOOM_JS" | sed 's/\\/\\\\/g; s/"/\\"/g')
        
        JS_CMD=$(cat <<EOF
{
    "id": 3,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "$JS_ESCAPED",
        "returnByValue": true
    }
}
EOF
        )
        
        JS_RESPONSE=$(echo "$JS_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
            error_log "JavaScript缩放也失败"
            exit 1
        }
        
        if echo "$JS_RESPONSE" | grep -q '"error"'; then
            error_log "无法设置页面缩放"
            exit 1
        fi
        
        info_log "使用CSS zoom设置缩放"
    else
        error_log "缩放错误: $ERROR_MSG"
        exit 1
    fi
fi

# 验证缩放设置（获取当前视口大小）
VERIFY_JS="({
    zoom: document.body.style.zoom || '1',
    width: window.innerWidth,
    height: window.innerHeight,
    devicePixelRatio: window.devicePixelRatio
})"

VERIFY_CMD=$(cat <<EOF
{
    "id": 4,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "$VERIFY_JS",
        "returnByValue": true
    }
}
EOF
)

debug_log "验证缩放设置..."

VERIFY_RESPONSE=$(echo "$VERIFY_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    debug_log "无法验证缩放设置"
}

if [ -n "$VERIFY_RESPONSE" ]; then
    WIDTH=$(echo "$VERIFY_RESPONSE" | sed -n 's/.*"width":\([0-9]*\).*/\1/p' | head -1)
    HEIGHT=$(echo "$VERIFY_RESPONSE" | sed -n 's/.*"height":\([0-9]*\).*/\1/p' | head -1)
    
    if [ -n "$WIDTH" ] && [ -n "$HEIGHT" ]; then
        debug_log "视口大小: ${WIDTH}x${HEIGHT}"
    fi
fi

success_log "缩放级别已设置为 ${ZOOM_PERCENT}%"