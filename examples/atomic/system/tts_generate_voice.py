#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["edge-tts"]
# ///
"""
Recipe: tts_generate_voice
Description: 使用 Edge TTS 生成语音配音
Created: 2025-11-26
Version: 1.0.0
"""

import asyncio
import json
import sys
from pathlib import Path


async def generate_voice_edge_tts(
    text: str,
    output_file: str,
    voice: str = "zh-CN-YunxiNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> dict:
    """使用 edge-tts 生成语音"""
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )

    await communicate.save(output_file)

    # 获取音频时长
    duration = await get_audio_duration(output_file)

    return {
        "file_path": str(Path(output_file).absolute()),
        "duration": duration,
        "file_size": Path(output_file).stat().st_size,
        "voice": voice,
        "rate": rate,
        "pitch": pitch
    }


async def get_audio_duration(file_path: str) -> float:
    """获取音频时长"""
    import subprocess

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
    except Exception:
        pass

    return 0


def speed_to_rate(speed: float) -> str:
    """将速度倍率转换为 edge-tts rate 格式"""
    # speed: 1.0 = 正常, 1.2 = 加快20%, 0.8 = 减慢20%
    percent = int((speed - 1.0) * 100)
    if percent >= 0:
        return f"+{percent}%"
    else:
        return f"{percent}%"


async def main_async():
    """异步主函数"""
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
    text = params.get("text")
    output_file = params.get("output_file")

    if not text:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: text"
        }), file=sys.stderr)
        sys.exit(1)

    if not output_file:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: output_file"
        }), file=sys.stderr)
        sys.exit(1)

    # 可选参数
    voice = params.get("voice", "zh-CN-YunxiNeural")
    speed = params.get("speed", 1.0)
    pitch = params.get("pitch", "+0Hz")

    # 转换速度格式
    rate = speed_to_rate(speed)

    try:
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"生成配音: voice={voice}, rate={rate}", file=sys.stderr)
        print(f"文本长度: {len(text)} 字符", file=sys.stderr)

        # 生成语音
        result = await generate_voice_edge_tts(
            text=text,
            output_file=output_file,
            voice=voice,
            rate=rate,
            pitch=pitch
        )

        # 输出结果
        output = {
            "success": True,
            **result
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


def main():
    """主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
