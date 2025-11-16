#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 高亮页面元素
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      为指定元素添加彩色边框高亮效果，支持自定义颜色和边框宽度，用于元素识别和重点展示
# 用法: ./cdp_highlight.sh <selector> [color] [width]
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
COLOR="${2:-#ff0000}"  # 默认红色
WIDTH="${3:-3}"         # 边框宽度

# 参数验证
if [ -z "$SELECTOR" ]; then
    error_log "缺少必需参数"
    echo "用法: $0 <selector> [color] [width]"
    echo "例如: $0 '.btn-primary' '#00ff00' 5"
    echo "      $0 '#header' '#0000ff'"
    echo "      $0 'div.content' '#ff0000' 4"
    exit 2
fi

# 验证颜色格式（简单验证）
if ! echo "$COLOR" | grep -qE '^#[0-9a-fA-F]{6}$|^#[0-9a-fA-F]{3}$|^[a-z]+$'; then
    error_log "无效的颜色格式: $COLOR"
    echo "颜色应为十六进制（如#ff0000）或颜色名称（如red）"
    exit 2
fi

# 验证边框宽度
if ! [[ "$WIDTH" =~ ^[0-9]+$ ]] || [ "$WIDTH" -lt 1 ] || [ "$WIDTH" -gt 20 ]; then
    error_log "无效的边框宽度: $WIDTH"
    echo "边框宽度应为1-20之间的数字"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

debug_log "高亮元素: $SELECTOR (颜色: $COLOR, 宽度: ${WIDTH}px)"

# 转义选择器
SELECTOR_ESCAPED=$(printf '%s' "$SELECTOR" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建JavaScript代码
JS_CODE="
(() => {
    // 移除之前的高亮
    document.querySelectorAll('.auvima-highlight').forEach(el => el.remove());
    
    // 获取目标元素
    const elements = document.querySelectorAll('$SELECTOR_ESCAPED');
    let count = 0;
    
    elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        const highlight = document.createElement('div');
        highlight.className = 'auvima-highlight';
        highlight.style.cssText = \`
            position: fixed;
            top: \${rect.top}px;
            left: \${rect.left}px;
            width: \${rect.width}px;
            height: \${rect.height}px;
            border: ${WIDTH}px solid ${COLOR};
            box-shadow: 0 0 10px ${COLOR};
            pointer-events: none;
            z-index: 99999;
            animation: auvima-pulse 1s infinite;
        \`;
        document.body.appendChild(highlight);
        count++;
    });
    
    // 添加动画
    if (!document.getElementById('auvima-styles')) {
        const style = document.createElement('style');
        style.id = 'auvima-styles';
        style.textContent = \`
            @keyframes auvima-pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        \`;
        document.head.appendChild(style);
    }
    
    return {
        success: true,
        message: count + ' elements highlighted',
        count: count,
        selector: '$SELECTOR_ESCAPED'
    };
})()
"

# 转义JavaScript代码
JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建CDP命令
HIGHLIGHT_CMD=$(cat <<EOF
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
RESPONSE=$(echo "$HIGHLIGHT_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "高亮操作失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "高亮错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"result"'; then
    COUNT=$(echo "$RESPONSE" | sed -n 's/.*"count":\([0-9]*\).*/\1/p' | head -1)
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    
    if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
        success_log "$MESSAGE"
    elif [ "$COUNT" = "0" ]; then
        info_log "未找到匹配的元素: $SELECTOR"
    else
        info_log "高亮操作完成"
    fi
else
    error_log "无效的响应格式"
    exit 1
fi