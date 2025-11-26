#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Recipe: video_add_audio_track
Description: 将音频轨道添加到视频文件
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
    return 0


def add_audio_to_video(
    video_file: str,
    audio_file: str,
    output_file: str,
    replace_audio: bool = True
) -> dict:
    """将音频添加到视频"""

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
    ]

    if replace_audio:
        # 替换原音轨：使用视频流和新音频流
        # 不使用 -shortest，保留视频完整时长，音频播完后自然静音
        cmd.extend([
            "-map", "0:v:0",  # 第一个输入的视频流
            "-map", "1:a:0",  # 第二个输入的音频流
            "-c:v", "copy",   # 视频直接复制
            "-c:a", "aac",    # 音频编码为 AAC
        ])
    else:
        # 混合音轨：保留原音轨并添加新音轨
        cmd.extend([
            "-map", "0:v:0",
            "-map", "0:a:0?",  # 原音频（如果存在）
            "-map", "1:a:0",   # 新音频
            "-c:v", "copy",
            "-c:a", "aac",
        ])

    cmd.append(output_file)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 合并失败: {result.stderr}")

    return {"command": " ".join(cmd)}


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
    output_file = params.get("output_file")

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

    if not output_file:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: output_file"
        }), file=sys.stderr)
        sys.exit(1)

    # 可选参数
    replace_audio = params.get("replace_audio", True)

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

        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 获取输入文件信息
        video_duration = get_media_duration(video_file)
        audio_duration = get_media_duration(audio_file)

        print(f"视频时长: {video_duration:.2f}s", file=sys.stderr)
        print(f"音频时长: {audio_duration:.2f}s", file=sys.stderr)

        # 合并音视频
        merge_info = add_audio_to_video(
            video_file, audio_file, output_file, replace_audio
        )

        # 获取输出文件信息
        output_duration = get_media_duration(output_file)
        output_size = output_path.stat().st_size if output_path.exists() else 0

        # 输出结果
        result = {
            "success": True,
            "file_path": str(output_path.absolute()),
            "duration": output_duration,
            "file_size": output_size,
            "input_video_duration": video_duration,
            "input_audio_duration": audio_duration,
            "replace_audio": replace_audio
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
