#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyobjc-framework-Quartz"]
# ///
"""
Recipe: macos_video_screen_crop_record
Description: macOS 专用 - 屏幕区域录制（ffmpeg crop 方式，窗口被遮挡时无法正确录制）
Created: 2025-11-26
Version: 1.2.0
Note: 如需真正的窗口级录制，请使用 obs_video_browser_window_record
"""

import json
import subprocess
import sys
import platform
from pathlib import Path


def check_platform():
    """检查是否在 macOS 上运行"""
    if platform.system() != "Darwin":
        raise RuntimeError(f"此 Recipe 仅支持 macOS，当前系统: {platform.system()}")


def check_ffmpeg():
    """检查 ffmpeg 是否可用"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError("ffmpeg 不可用")
        return True
    except FileNotFoundError:
        raise RuntimeError("ffmpeg 未安装，请运行: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffmpeg 检查超时")


def get_chrome_window_bounds() -> dict:
    """使用 Quartz CGWindowListCopyWindowInfo 获取 Chrome 窗口边界

    Returns:
        dict: {"x": int, "y": int, "width": int, "height": int}

    Raises:
        RuntimeError: 如果找不到 Chrome 窗口
    """
    import Quartz

    # 获取所有屏幕上可见的窗口
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )

    # 查找 Chrome 主窗口 (layer == 0 表示普通窗口，非菜单/弹出)
    chrome_windows = []
    for win in windows:
        owner = win.get('kCGWindowOwnerName', '')
        layer = win.get('kCGWindowLayer', -1)

        if ('Chrome' in owner or 'Google Chrome' in owner) and layer == 0:
            bounds = win.get('kCGWindowBounds', {})
            width = int(bounds.get('Width', 0))
            height = int(bounds.get('Height', 0))

            # 过滤掉太小的窗口（如 DevTools 弹出窗口等）
            if width > 200 and height > 200:
                chrome_windows.append({
                    "x": int(bounds.get('X', 0)),
                    "y": int(bounds.get('Y', 0)),
                    "width": width,
                    "height": height,
                    "title": win.get('kCGWindowName', 'Unknown')
                })

    if not chrome_windows:
        raise RuntimeError("未找到 Chrome 浏览器窗口，请确保 Chrome 已打开且可见")

    # 返回第一个（最前面的）Chrome 窗口
    return chrome_windows[0]


def get_screen_info() -> dict:
    """获取主屏幕信息"""
    import Quartz

    main_display = Quartz.CGMainDisplayID()
    width = Quartz.CGDisplayPixelsWide(main_display)
    height = Quartz.CGDisplayPixelsHigh(main_display)

    return {
        "width": width,
        "height": height,
        "display_id": main_display
    }


def get_screen_device_index() -> str:
    """获取屏幕录制设备索引"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True, text=True, timeout=10
        )
        output = result.stderr

        import re
        for line in output.split('\n'):
            if 'Capture screen' in line:
                match = re.search(r'\[(\d+)\]\s+Capture screen', line)
                if match:
                    return match.group(1)
        return "1"
    except Exception as e:
        print(f"警告: 获取设备索引失败: {e}，使用默认值 1", file=sys.stderr)
        return "1"


def record_chrome_window(
    output_file: str,
    duration: float,
    framerate: int = 30,
    capture_cursor: bool = True
) -> dict:
    """录制 Chrome 浏览器窗口

    使用 ffmpeg 全屏录制 + crop 滤镜裁剪到 Chrome 窗口区域
    """

    # 获取 Chrome 窗口边界
    window_bounds = get_chrome_window_bounds()
    print(f"Chrome 窗口: {window_bounds['title']}", file=sys.stderr)
    print(f"窗口位置: X={window_bounds['x']}, Y={window_bounds['y']}", file=sys.stderr)
    print(f"窗口大小: {window_bounds['width']}x{window_bounds['height']}", file=sys.stderr)

    # 获取屏幕信息
    screen_info = get_screen_info()
    print(f"屏幕大小: {screen_info['width']}x{screen_info['height']}", file=sys.stderr)

    # 获取屏幕设备索引
    screen_index = get_screen_device_index()
    print(f"屏幕设备索引: {screen_index}", file=sys.stderr)

    # 计算 crop 参数
    # crop=w:h:x:y - 从位置 (x,y) 裁剪 w*h 的区域
    crop_w = window_bounds['width']
    crop_h = window_bounds['height']
    crop_x = window_bounds['x']
    crop_y = window_bounds['y']

    # 确保裁剪区域不超出屏幕边界
    if crop_x + crop_w > screen_info['width']:
        crop_w = screen_info['width'] - crop_x
    if crop_y + crop_h > screen_info['height']:
        crop_h = screen_info['height'] - crop_y

    # 确保宽高是偶数（H.264 编码要求）
    crop_w = crop_w - (crop_w % 2)
    crop_h = crop_h - (crop_h % 2)

    crop_filter = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
    print(f"Crop 滤镜: {crop_filter}", file=sys.stderr)

    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-framerate", str(framerate),
    ]

    # 光标捕获选项
    if capture_cursor:
        cmd.extend(["-capture_cursor", "1"])
    else:
        cmd.extend(["-capture_cursor", "0"])

    # 输入设备（仅视频，不录音频）
    cmd.extend(["-i", f"{screen_index}:"])

    # 视频滤镜：裁剪到窗口区域
    cmd.extend(["-vf", crop_filter])

    # 输出编码设置
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_file
    ])

    print(f"执行命令: {' '.join(cmd)}", file=sys.stderr)
    print(f"录制 {duration} 秒...", file=sys.stderr)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=duration + 60
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 录制失败: {result.stderr}")

    return {
        "command": " ".join(cmd),
        "screen_device": screen_index,
        "window_bounds": window_bounds,
        "crop_filter": crop_filter
    }


def get_video_info(file_path: str) -> dict:
    """获取视频信息"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

        return {
            "duration": float(fmt.get("duration", 0)),
            "file_size": int(fmt.get("size", 0)),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "codec": video_stream.get("codec_name", "unknown"),
            "bitrate": int(fmt.get("bit_rate", 0))
        }
    return {"duration": 0, "file_size": 0}


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
    duration = params.get("duration")
    output_file = params.get("output_file")

    if not duration:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: duration"
        }), file=sys.stderr)
        sys.exit(1)

    if not output_file:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: output_file"
        }), file=sys.stderr)
        sys.exit(1)

    # 可选参数
    framerate = params.get("framerate", 30)
    capture_cursor = params.get("capture_cursor", True)

    try:
        # 检查平台
        check_platform()

        # 检查 ffmpeg
        check_ffmpeg()

        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 录制 Chrome 窗口
        print(f"开始录制 Chrome 浏览器窗口...", file=sys.stderr)
        record_info = record_chrome_window(
            output_file, duration, framerate, capture_cursor
        )

        # 获取视频信息
        video_info = get_video_info(output_file)

        # 输出结果
        result = {
            "success": True,
            "file_path": str(output_path.absolute()),
            "duration": video_info.get("duration", 0),
            "file_size": video_info.get("file_size", 0),
            "resolution": {
                "width": video_info.get("width", 0),
                "height": video_info.get("height", 0)
            },
            "codec": video_info.get("codec", "unknown"),
            "bitrate": video_info.get("bitrate", 0),
            "platform": "macos",
            "window_bounds": record_info.get("window_bounds"),
            "record_info": record_info
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
