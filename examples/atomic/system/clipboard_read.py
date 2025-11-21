#!/usr/bin/env python3
"""
Recipe: 读取剪贴板内容
运行时: python
输入参数: 无
输出: JSON 格式的剪贴板内容
"""

import json
import sys


def read_clipboard():
    """读取剪贴板内容并返回 JSON 格式"""
    try:
        import pyperclip
        content = pyperclip.paste()
        return {
            "success": True,
            "data": {
                "content": content,
                "length": len(content)
            }
        }
    except ImportError:
        return {
            "success": False,
            "error": {
                "type": "DependencyError",
                "message": "pyperclip module not found. Install with: pip install pyperclip"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }


if __name__ == "__main__":
    result = read_clipboard()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)
