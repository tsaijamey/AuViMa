#!/bin/bash
# AuViMa项目 - 自动化视觉管理系统
# 功能: 等待元素出现
# 背景: 本脚本是AuViMa项目的一部分，用于自动化控制Chrome浏览器进行网页操作和测试
#      等待指定CSS选择器的元素在页面上出现，支持超时设置，用于同步等待动态加载内容
# 用法: ./cdp_wait.sh <selector> [timeout_seconds]
# 标准化: 使用websocat和CDP的Runtime.evaluate进行高效轮询

set -euo pipefail

# 加载通用函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cdp_common.sh" 2>/dev/null || {
    echo "错误：无法加载通用函数库" >&2
    exit 1
}

# 参数处理
SELECTOR="${1:-}"
TIMEOUT="${2:-30}"  # 默认30秒超时

# 参数验证
if [ -z "$SELECTOR" ]; then
    error_log "缺少必需参数"
    echo "用法: $0 <selector> [timeout_seconds]"
    echo "例如: $0 \"#loading\" 10"
    echo "      $0 \"div.content\""
    echo "      $0 \"button:enabled\" 60"
    exit 2
fi

# 验证超时参数
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [ "$TIMEOUT" -lt 1 ]; then
    error_log "无效的超时值: $TIMEOUT"
    echo "超时值必须是大于0的整数"
    exit 2
fi

# 检查CDP环境
check_cdp_environment || exit $?

# 获取WebSocket URL
WS_URL=$(get_websocket_url) || {
    error_log "无法获取WebSocket URL"
    exit 1
}

info_log "等待元素: $SELECTOR (最多${TIMEOUT}秒)"

# 转义选择器
SELECTOR_ESCAPED=$(printf '%s' "$SELECTOR" | sed 's/\\/\\\\/g; s/"/\\"/g')

# 使用更智能的等待策略
# 创建一个JavaScript函数来等待元素
WAIT_JS="
(async function() {
    const selector = '$SELECTOR_ESCAPED';
    const timeout = ${TIMEOUT}000; // 转换为毫秒
    const checkInterval = 100; // 每100ms检查一次
    const startTime = Date.now();
    
    // 先检查元素是否已经存在
    let element = document.querySelector(selector);
    if (element) {
        return {
            found: true,
            message: 'Element already present',
            selector: selector,
            tagName: element.tagName,
            visible: element.offsetWidth > 0 && element.offsetHeight > 0
        };
    }
    
    // 使用MutationObserver监听DOM变化
    return new Promise((resolve) => {
        let resolved = false;
        
        // 设置超时
        const timeoutId = setTimeout(() => {
            if (!resolved) {
                resolved = true;
                observer.disconnect();
                resolve({
                    found: false,
                    message: 'Timeout waiting for element',
                    selector: selector,
                    elapsed: Date.now() - startTime
                });
            }
        }, timeout);
        
        // 创建观察者
        const observer = new MutationObserver(() => {
            if (resolved) return;
            
            const element = document.querySelector(selector);
            if (element) {
                resolved = true;
                clearTimeout(timeoutId);
                observer.disconnect();
                resolve({
                    found: true,
                    message: 'Element appeared',
                    selector: selector,
                    tagName: element.tagName,
                    visible: element.offsetWidth > 0 && element.offsetHeight > 0,
                    elapsed: Date.now() - startTime
                });
            }
        });
        
        // 开始观察
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'id', 'style']
        });
        
        // 定期检查（作为备份机制）
        const intervalId = setInterval(() => {
            if (resolved) {
                clearInterval(intervalId);
                return;
            }
            
            const element = document.querySelector(selector);
            if (element) {
                resolved = true;
                clearTimeout(timeoutId);
                clearInterval(intervalId);
                observer.disconnect();
                resolve({
                    found: true,
                    message: 'Element found by polling',
                    selector: selector,
                    tagName: element.tagName,
                    visible: element.offsetWidth > 0 && element.offsetHeight > 0,
                    elapsed: Date.now() - startTime
                });
            }
        }, checkInterval);
    });
})()
"

# 构建CDP命令
WAIT_CMD=$(cat <<EOF
{
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "$WAIT_JS",
        "awaitPromise": true,
        "returnByValue": true,
        "timeout": ${TIMEOUT}000
    }
}
EOF
)

debug_log "开始等待元素..."

# 发送命令并等待响应
RESPONSE=$(echo "$WAIT_CMD" | websocat -t -n1 -B $((TIMEOUT + 5))000000 "$WS_URL" 2>/dev/null) || {
    error_log "等待操作失败"
    exit 1
}

debug_log "响应: ${RESPONSE:0:200}..."

# 检查结果
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(parse_json "$RESPONSE" '.error.message' 2>/dev/null || echo "未知错误")
    error_log "等待错误: $ERROR_MSG"
    exit 1
fi

# 解析结果
if echo "$RESPONSE" | grep -q '"found":true'; then
    # 提取详细信息
    TAG_NAME=$(echo "$RESPONSE" | sed -n 's/.*"tagName":"\([^"]*\)".*/\1/p' | head -1)
    VISIBLE=$(echo "$RESPONSE" | sed -n 's/.*"visible":\([a-z]*\).*/\1/p' | head -1)
    ELAPSED=$(echo "$RESPONSE" | sed -n 's/.*"elapsed":\([0-9]*\).*/\1/p' | head -1)
    MESSAGE=$(echo "$RESPONSE" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p' | head -1)
    
    if [ -n "$ELAPSED" ]; then
        ELAPSED_SEC=$((ELAPSED / 1000))
        info_log "$MESSAGE (${ELAPSED_SEC}秒)"
    fi
    
    if [ "$VISIBLE" = "false" ]; then
        info_log "注意: 元素存在但不可见"
    fi
    
    success_log "元素已出现: $SELECTOR"
    exit 0
elif echo "$RESPONSE" | grep -q '"found":false'; then
    ELAPSED=$(echo "$RESPONSE" | sed -n 's/.*"elapsed":\([0-9]*\).*/\1/p' | head -1)
    if [ -n "$ELAPSED" ]; then
        ELAPSED_SEC=$((ELAPSED / 1000))
        error_log "等待超时 (${ELAPSED_SEC}秒): $SELECTOR"
    else
        error_log "等待超时: $SELECTOR"
    fi
    exit 1
else
    error_log "无效的响应格式"
    exit 1
fi