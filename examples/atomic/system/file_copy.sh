#!/bin/bash
# Recipe: 复制文件
# 运行时: shell
# 输入参数: source_path, dest_path
# 输出: JSON 格式的操作结果

set -euo pipefail

# 解析输入参数（JSON 格式）
if [ $# -eq 0 ]; then
    echo '{"success": false, "error": {"type": "ArgumentError", "message": "Missing required parameter: params JSON string"}}'
    exit 1
fi

PARAMS_JSON="$1"

# 提取参数
SOURCE=$(echo "$PARAMS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('source_path', ''))")
DEST=$(echo "$PARAMS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('dest_path', ''))")

# 验证参数
if [ -z "$SOURCE" ] || [ -z "$DEST" ]; then
    echo '{"success": false, "error": {"type": "ValidationError", "message": "Missing required parameters: source_path and dest_path"}}'
    exit 1
fi

# 检查源文件是否存在
if [ ! -f "$SOURCE" ]; then
    echo "{\"success\": false, \"error\": {\"type\": \"FileNotFoundError\", \"message\": \"Source file not found: $SOURCE\"}}"
    exit 1
fi

# 执行复制操作
if cp "$SOURCE" "$DEST" 2>/dev/null; then
    SOURCE_SIZE=$(stat -c%s "$SOURCE" 2>/dev/null || stat -f%z "$SOURCE" 2>/dev/null)
    echo "{\"success\": true, \"data\": {\"source\": \"$SOURCE\", \"destination\": \"$DEST\", \"size_bytes\": $SOURCE_SIZE, \"operation\": \"copy\"}}"
    exit 0
else
    echo "{\"success\": false, \"error\": {\"type\": \"CopyError\", \"message\": \"Failed to copy file from $SOURCE to $DEST\"}}"
    exit 1
fi
