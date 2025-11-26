#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Recipe: video_validate_av_sync
Description: 验证音视频时长是否同步
Created: 2025-11-26
Version: 1.0.0
"""

import json
import subprocess
import sys
from pathlib import Path


def get_media_duration(file_path: str) -> float:
    """获取媒体文件时长"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))

    raise RuntimeError(f"无法获取文件时长: {file_path}")


def main():
    """主函数"""
    # 解析参数
    if len(sys.argv) < 2:
        params = {}
    else:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "error": f"参数 JSON 解析失败: {e}"
            }), file=sys.stderr)
            sys.exit(1)

    # 验证必需参数
    video_file = params.get("video_file")
    audio_file = params.get("audio_file")

    if not video_file:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: video_file"
        }), file=sys.stderr)
        sys.exit(1)

    if not audio_file:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: audio_file"
        }), file=sys.stderr)
        sys.exit(1)

    # 可选参数
    tolerance = params.get("tolerance", 0.5)  # 默认容差 0.5 秒

    try:
        # 验证输入文件存在
        if not Path(video_file).exists():
            print(json.dumps({
                "success": False,
                "error": f"视频文件不存在: {video_file}"
            }), file=sys.stderr)
            sys.exit(1)

        if not Path(audio_file).exists():
            print(json.dumps({
                "success": False,
                "error": f"音频文件不存在: {audio_file}"
            }), file=sys.stderr)
            sys.exit(1)

        # 获取时长
        video_duration = get_media_duration(video_file)
        audio_duration = get_media_duration(audio_file)

        # 计算差异
        difference = video_duration - audio_duration
        abs_difference = abs(difference)

        # 判断是否同步
        # 同步条件：视频时长 >= 音频时长（音频短于视频是正常的，只需要视频能容纳音频）
        # 只有音频比视频长才算不同步
        is_synced = video_duration >= audio_duration

        # 生成建议
        suggestions = []
        if video_duration < audio_duration:
            shortage = audio_duration - video_duration
            suggestions.append(f"视频时长不足，需要延长 {shortage:.2f} 秒")
            suggestions.append("建议：增加视频 duration 或加快音频语速")

        # 输出结果
        result = {
            "success": True,
            "video_duration": round(video_duration, 3),
            "audio_duration": round(audio_duration, 3),
            "difference": round(difference, 3),
            "is_synced": is_synced,
            "tolerance": tolerance,
            "video_file": video_file,
            "audio_file": audio_file
        }

        if suggestions:
            result["suggestions"] = suggestions

        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 根据同步状态设置退出码
        sys.exit(0 if is_synced else 1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
