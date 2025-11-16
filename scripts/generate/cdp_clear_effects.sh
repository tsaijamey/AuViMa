#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 清除所有视觉效果
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      清除页面上所有由AuViMa脚本添加的视觉效果元素，如高亮、标注、聚光灯等
# 用法: ./cdp_clear_effects.sh
# 标准化: 使用websocat和CDP的Runtime.evaluate

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../share/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

debug_log "清除所有AuViMa视觉效果..."

# 构建JavaScript代码
JS_CODE="
(() => {
    // 清除所有AuViMa添加的元素
    const effectSelectors = [
        '.auvima-highlight',
        '.auvima-spotlight', 
        '.auvima-annotation',
        '.auvima-pointer',
        '.auvima-overlay',
        '.auvima-focus',
        '.auvima-tooltip',
        '.auvima-marker'
    ];
    
    let totalRemoved = 0;
    let removedByType = {};
    
    // 统计并移除各类效果
    effectSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        const count = elements.length;
        if (count > 0) {
            const className = selector.substring(1); // 移除点号
            removedByType[className] = count;
            elements.forEach(el => el.remove());
            totalRemoved += count;
        }
    });
    
    // 清除添加的样式
    const styleSelectors = [
        '#auvima-styles',
        '#auvima-annotation-styles',
        '#auvima-pointer-styles',
        '#auvima-spotlight-styles',
        '#auvima-tooltip-styles'
    ];
    
    let stylesRemoved = 0;
    styleSelectors.forEach(selector => {
        const style = document.querySelector(selector);
        if (style) {
            style.remove();
            stylesRemoved++;
        }
    });
    
    // 移除可能存在的事件监听器（通过重新加载窗口resize处理器）
    const spotlights = document.querySelectorAll('.auvima-spotlight');
    spotlights.forEach(spotlight => {
        if (spotlight.resizeHandler) {
            window.removeEventListener('resize', spotlight.resizeHandler);
        }
    });
    
    return {
        success: true,
        totalRemoved: totalRemoved,
        stylesRemoved: stylesRemoved,
        removedByType: removedByType,
        message: totalRemoved > 0 ? 
            'Cleared ' + totalRemoved + ' effects and ' + stylesRemoved + ' styles' :
            'No effects to clear'
    };
})()
"

# 转义JavaScript代码
JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建CDP命令
CLEAR_CMD=$(cat <<EOF
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

# 发送命令
RESPONSE=$(echo "$CLEAR_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "清除效果失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "清除错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    TOTAL_REMOVED=$(echo "$RESPONSE" | sed -n 's/.*"totalRemoved":\([0-9]*\).*/\1/p' | head -1)
    STYLES_REMOVED=$(echo "$RESPONSE" | sed -n 's/.*"stylesRemoved":\([0-9]*\).*/\1/p' | head -1)
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    
    if [ -n "$TOTAL_REMOVED" ] && [ "$TOTAL_REMOVED" -gt 0 ]; then
        # 尝试解析详细信息
        if echo "$RESPONSE" | grep -q '"removedByType"'; then
            debug_log "清除详情:"
            # 解析各类型效果的数量
            for effect in highlight spotlight annotation pointer overlay focus tooltip marker; do
                COUNT=$(echo "$RESPONSE" | sed -n "s/.*\"auvima-$effect\":\([0-9]*\).*/\1/p" | head -1)
                if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
                    debug_log "  - $effect: $COUNT个"
                fi
            done
        fi
        
        success_log "已清除 ${TOTAL_REMOVED} 个效果元素"
        if [ -n "$STYLES_REMOVED" ] && [ "$STYLES_REMOVED" -gt 0 ]; then
            info_log "已清除 ${STYLES_REMOVED} 个样式表"
        fi
    elif [ "$TOTAL_REMOVED" = "0" ]; then
        info_log "没有需要清除的效果"
    else
        info_log "$MESSAGE"
    fi
else
    error_log "无效的响应格式"
    exit 1
fi