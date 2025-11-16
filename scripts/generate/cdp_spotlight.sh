#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 聚光灯效果 - 突出显示元素，其他区域变暗
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      为指定元素创建聚光灯效果，突出显示目标区域同时将周围区域变暗，用于焦点展示
# 用法: ./cdp_spotlight.sh <selector> [opacity]
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
OPACITY="${2:-0.8}"  # 遮罩透明度

# 参数验证
if [ -z "$SELECTOR" ]; then
    error_log "缺少必需参数"
    echo "用法: $0 <selector> [opacity]"
    echo "例如: $0 '#main-content' 0.7"
    echo "      $0 '.hero-section' 0.9"
    echo "      $0 'article' 0.6"
    exit 2
fi

# 验证透明度值
if ! echo "$OPACITY" | grep -qE '^[0-9]+(\.[0-9]+)?$' || \
   (( $(echo "$OPACITY < 0" | bc -l 2>/dev/null || echo "1") )) || \
   (( $(echo "$OPACITY > 1" | bc -l 2>/dev/null || echo "0") )); then
    error_log "无效的透明度值: $OPACITY"
    echo "透明度值应为0-1之间的数字（0=透明, 1=不透明）"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

debug_log "创建聚光灯效果: $SELECTOR (透明度: $OPACITY)"

# 转义选择器
SELECTOR_ESCAPED=$(printf '%s' "$SELECTOR" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建JavaScript代码
JS_CODE="
(() => {
    // 移除之前的遮罩
    document.querySelectorAll('.auvima-spotlight').forEach(el => el.remove());
    
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
    
    // 创建聚光灯容器（使用box-shadow创建镂空效果）
    const spotlight = document.createElement('div');
    spotlight.className = 'auvima-spotlight';
    spotlight.style.cssText = \`
        position: fixed;
        top: \${rect.top - 10}px;
        left: \${rect.left - 10}px;
        width: \${rect.width + 20}px;
        height: \${rect.height + 20}px;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, ${OPACITY});
        border-radius: 5px;
        pointer-events: none;
        z-index: 99997;
    \`;
    
    document.body.appendChild(spotlight);
    
    // 添加渐变动画效果
    const style = document.createElement('style');
    style.id = 'auvima-spotlight-styles';
    style.textContent = \`
        .auvima-spotlight {
            animation: auvima-spotlight-fade 0.5s ease-in-out;
        }
        @keyframes auvima-spotlight-fade {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
    \`;
    document.head.appendChild(style);
    
    // 滚动到元素
    element.scrollIntoView({behavior: 'smooth', block: 'center'});
    
    // 处理窗口大小变化
    const resizeHandler = () => {
        const newRect = element.getBoundingClientRect();
        spotlight.style.top = \`\${newRect.top - 10}px\`;
        spotlight.style.left = \`\${newRect.left - 10}px\`;
        spotlight.style.width = \`\${newRect.width + 20}px\`;
        spotlight.style.height = \`\${newRect.height + 20}px\`;
    };
    
    // 监听窗口大小变化
    window.addEventListener('resize', resizeHandler);
    
    // 保存处理函数以便移除
    spotlight.resizeHandler = resizeHandler;
    
    return {
        success: true,
        message: 'Spotlight effect created',
        selector: '$SELECTOR_ESCAPED',
        elementTag: element.tagName.toLowerCase(),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
    };
})()
"

# 转义JavaScript代码
JS_ESCAPED=$(printf '%s' "$JS_CODE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 构建CDP命令
SPOTLIGHT_CMD=$(cat <<EOF
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
RESPONSE=$(echo "$SPOTLIGHT_CMD" | websocat -t -n1 "$WS_URL" 2>/dev/null) || {
    error_log "聚光灯效果失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "聚光灯错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    ELEMENT_TAG=$(echo "$RESPONSE" | sed -n 's/.*"elementTag":"\([^"]*\)".*/\1/p' | head -1)
    WIDTH=$(echo "$RESPONSE" | sed -n 's/.*"width":\([0-9]*\).*/\1/p' | head -1)
    HEIGHT=$(echo "$RESPONSE" | sed -n 's/.*"height":\([0-9]*\).*/\1/p' | head -1)
    
    if [ -n "$ELEMENT_TAG" ]; then
        debug_log "元素: <$ELEMENT_TAG> ${WIDTH}x${HEIGHT}px"
    fi
    
    success_log "聚光灯效果已创建: $SELECTOR"
    info_log "遮罩透明度: $OPACITY"
elif echo "$RESPONSE" | grep -q '"success":false'; then
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    error_log "元素未找到: $SELECTOR"
    exit 1
else
    error_log "无效的响应格式"
    exit 1
fi