#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 添加动态指针效果，模拟鼠标移动到元素
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      创建动态鼠标指针动画，模拟从屏幕角落移动到目标元素的过程，用于操作演示和用户指导
# 用法: ./cdp_pointer.sh <selector> [duration]
# 标准化: 使用websocat和CDP的Runtime.evaluate

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../share/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 参数处理
SELECTOR="${1:-}"
DURATION="${2:-2}"  # 动画持续时间（秒）

# 参数验证
if [ -z "$SELECTOR" ]; then
    error_log "缺少必需参数"
    echo "用法: $0 <selector> [duration]"
    echo "例如: $0 'button.submit' 3"
    echo "      $0 '#login-btn' 2"
    echo "      $0 '.menu-item' 1.5"
    exit 2
fi

# 验证持续时间
if ! echo "$DURATION" | grep -qE '^[0-9]+(\.[0-9]+)?$' || \
   (( $(echo "$DURATION < 0.5" | bc -l 2>/dev/null || echo "1") )) || \
   (( $(echo "$DURATION > 10" | bc -l 2>/dev/null || echo "0") )); then
    error_log "无效的持续时间: $DURATION"
    echo "持续时间应为0.5-10秒之间的数字"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

debug_log "创建指针动画: $SELECTOR (持续${DURATION}秒)"

# 转义选择器
SELECTOR_ESCAPED=$(printf '%s' "$SELECTOR" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建JavaScript代码
JS_CODE="
(() => {
    // 获取目标元素
    const element = document.querySelector('$SELECTOR_ESCAPED');
    if (!element) {
        return {
            success: false,
            message: 'Element not found',
            selector: '$SELECTOR_ESCAPED'
        };
    }
    
    const rect = element.getBoundingClientRect();
    const targetX = rect.left + rect.width/2;
    const targetY = rect.top + rect.height/2;
    
    // 创建指针
    const pointer = document.createElement('div');
    pointer.className = 'auvima-pointer';
    pointer.innerHTML = \`
        <svg width='30' height='30' viewBox='0 0 30 30'>
            <path d='M 5 5 L 25 12 L 12 25 Z' fill='#ff4444' stroke='#fff' stroke-width='2'/>
        </svg>
    \`;
    
    // 起始位置（屏幕右上角）
    const startX = window.innerWidth - 100;
    const startY = 100;
    
    pointer.style.cssText = \`
        position: fixed;
        left: \${startX}px;
        top: \${startY}px;
        width: 30px;
        height: 30px;
        z-index: 100000;
        pointer-events: none;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
        animation: auvima-move-pointer ${DURATION}s ease-in-out;
    \`;
    
    document.body.appendChild(pointer);
    
    // 添加动画样式
    const style = document.createElement('style');
    style.id = 'auvima-pointer-styles';
    style.textContent = \`
        @keyframes auvima-move-pointer {
            0% {
                left: \${startX}px;
                top: \${startY}px;
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                left: \${targetX - 15}px;
                top: \${targetY - 15}px;
                opacity: 1;
            }
            100% {
                left: \${targetX - 15}px;
                top: \${targetY - 15}px;
                opacity: 0;
            }
        }
    \`;
    document.head.appendChild(style);
    
    // 移除指针
    setTimeout(() => {
        pointer.remove();
        style.remove();
    }, ${DURATION}000 + 500);
    
    // 滚动到元素
    element.scrollIntoView({behavior: 'smooth', block: 'center'});
    
    return {
        success: true,
        message: 'Pointer animation started',
        selector: '$SELECTOR_ESCAPED',
        targetX: Math.round(targetX),
        targetY: Math.round(targetY)
    };
})()
"

# 转义JavaScript代码
JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建CDP命令
POINTER_CMD=$(cat <<EOF
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
RESPONSE=$(echo "$POINTER_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "指针动画失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "指针动画错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    TARGET_X=$(echo "$RESPONSE" | sed -n 's/.*"targetX":\([0-9]*\).*/\1/p' | head -1)
    TARGET_Y=$(echo "$RESPONSE" | sed -n 's/.*"targetY":\([0-9]*\).*/\1/p' | head -1)
    
    if [ -n "$TARGET_X" ] && [ -n "$TARGET_Y" ]; then
        debug_log "目标位置: ($TARGET_X, $TARGET_Y)"
    fi
    
    success_log "指针动画已启动: $SELECTOR"
    info_log "动画持续${DURATION}秒"
elif echo "$RESPONSE" | grep -q '"success":false'; then
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    error_log "元素未找到: $SELECTOR"
    exit 1
else
    error_log "无效的响应格式"
    exit 1
fi