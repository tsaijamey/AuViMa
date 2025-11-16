#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 给指定元素添加边框高亮
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      通过给元素加边框来标注"当前看这里"的位置，用于界面说明和用户指导
# 用法: ./cdp_annotate.sh <selector> [color] [width]
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
COLOR="${2:-red}"      # 默认红色边框
WIDTH="${3:-2}"        # 默认2px边框

# 参数验证
if [ -z "$SELECTOR" ]; then
    error_log "缺少必需参数"
    echo "用法: $0 <selector> [color] [width]"
    echo "例如: $0 'button' blue 3"
    echo "      $0 '.class-name' green"
    echo "      $0 '#id' '#ff0000' 4"
    exit 2
fi

# 验证边框宽度
if ! [[ "$WIDTH" =~ ^[0-9]+$ ]] || [ "$WIDTH" -lt 1 ] || [ "$WIDTH" -gt 10 ]; then
    error_log "无效的边框宽度: $WIDTH"
    echo "边框宽度应为1-10之间的数字"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

debug_log "标注元素: $SELECTOR (边框: ${WIDTH}px $COLOR)"

# 转义选择器
SELECTOR_ESCAPED=$(printf '%s' "$SELECTOR" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建JavaScript代码 - 简单的边框标注
JS_CODE="
(function() {
    const selector = '$SELECTOR_ESCAPED';
    const elements = document.querySelectorAll(selector);
    
    if (elements.length === 0) {
        return {
            success: false,
            message: 'Element not found',
            selector: selector
        };
    }
    
    let count = 0;
    elements.forEach(el => {
        // 保存原始边框样式
        if (!el.hasAttribute('data-auvima-original-border')) {
            el.setAttribute('data-auvima-original-border', el.style.border || '');
        }
        
        // 设置新边框
        el.style.border = '${WIDTH}px solid ${COLOR}';
        el.classList.add('auvima-annotated');
        count++;
    });
    
    return {
        success: true,
        message: count + ' elements annotated',
        count: count,
        selector: selector
    };
})()
"

# 转义JavaScript代码
JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建CDP命令
ANNOTATE_CMD=$(cat <<EOF
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
RESPONSE=$(echo "$ANNOTATE_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "标注操作失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "标注错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$RESPONSE" | sed -n 's/.*"count":\([0-9]*\).*/\1/p' | head -1)
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    
    if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
        success_log "已标注 ${COUNT} 个元素: $SELECTOR"
        info_log "边框样式: ${WIDTH}px $COLOR"
    else
        info_log "标注操作完成"
    fi
elif echo "$RESPONSE" | grep -q '"success":false'; then
    error_log "元素未找到: $SELECTOR"
    exit 1
else
    error_log "无效的响应格式"
    exit 1
fi