#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["dbus-python"]
# ///
"""
Recipe: linux_video_screen_crop_record
Description: Linux 专用 - 屏幕区域录制（ffmpeg crop 方式，窗口被遮挡时无法正确录制）
Created: 2025-11-26
Version: 1.2.0
Note: 如需真正的窗口级录制，请使用 obs_video_browser_window_record
"""

import json
import subprocess
import sys
import re
from pathlib import Path


def get_chrome_window_geometry_x11() -> dict:
    """获取 Chrome 窗口几何信息 (X11)"""
    try:
        # 使用 xdotool 查找 Chrome 窗口
        result = subprocess.run(
            ["xdotool", "search", "--name", "Chrome"],
            capture_output=True, text=True, timeout=5
        )
        window_ids = result.stdout.strip().split('\n')

        if not window_ids or not window_ids[0]:
            raise RuntimeError("未找到 Chrome 窗口")

        window_id = window_ids[0]

        # 获取窗口几何信息
        result = subprocess.run(
            ["xdotool", "getwindowgeometry", "--shell", window_id],
            capture_output=True, text=True, timeout=5
        )

        geometry = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                geometry[key] = int(value)

        return {
            "x": geometry.get("X", 0),
            "y": geometry.get("Y", 0),
            "width": geometry.get("WIDTH", 1280),
            "height": geometry.get("HEIGHT", 960),
            "window_id": window_id
        }
    except FileNotFoundError:
        raise RuntimeError("xdotool 未安装，请运行: sudo apt install xdotool")
    except subprocess.TimeoutExpired:
        raise RuntimeError("获取窗口信息超时")


def get_chrome_window_geometry_wayland() -> dict:
    """获取 Chrome 窗口几何信息 (Wayland) - 使用默认值"""
    # Wayland 下难以获取窗口位置，使用默认值
    return {
        "x": 0,
        "y": 0,
        "width": 1280,
        "height": 960,
        "window_id": "wayland"
    }


def get_display_server() -> str:
    """检测显示服务器类型"""
    import os
    xdg_session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if xdg_session == "wayland":
        return "wayland"
    elif xdg_session == "x11":
        return "x11"
    # 尝试检测 DISPLAY 环境变量
    if os.environ.get("DISPLAY"):
        return "x11"
    return "wayland"


def record_screen_x11(
    output_file: str,
    duration: float,
    geometry: dict,
    framerate: int = 30,
    capture_cursor: bool = True
) -> dict:
    """使用 ffmpeg 录制屏幕 (X11)"""

    display = subprocess.run(
        ["bash", "-c", "echo $DISPLAY"],
        capture_output=True, text=True
    ).stdout.strip() or ":0"

    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg", "-y",
        "-f", "x11grab",
        "-framerate", str(framerate),
        "-video_size", f"{geometry['width']}x{geometry['height']}",
        "-i", f"{display}+{geometry['x']},{geometry['y']}",
    ]

    if capture_cursor:
        cmd.extend(["-draw_mouse", "1"])
    else:
        cmd.extend(["-draw_mouse", "0"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-t", str(duration),
        output_file
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 30)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 录制失败: {result.stderr}")

    return {"command": " ".join(cmd)}


def get_primary_monitor_geometry() -> dict:
    """获取主显示器几何信息"""
    import subprocess
    try:
        result = subprocess.run(
            ["xrandr"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if ' connected primary ' in line:
                # 解析: eDP-1 connected primary 1600x1000+0+440
                import re
                match = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                if match:
                    return {
                        "width": int(match.group(1)),
                        "height": int(match.group(2)),
                        "x": int(match.group(3)),
                        "y": int(match.group(4))
                    }
    except Exception:
        pass
    # 默认值
    return {"x": 0, "y": 0, "width": 1920, "height": 1080}


def record_screen_wayland(
    output_file: str,
    duration: float,
    geometry: dict,
    framerate: int = 30,
    capture_cursor: bool = True
) -> dict:
    """使用 GNOME Screencast D-Bus 录制屏幕 (Wayland/GNOME)

    使用 ScreencastArea 录制主显示器区域，避免录制整个多显示器桌面
    """
    import time
    import dbus

    output_path = Path(output_file).absolute()
    is_mp4 = output_file.lower().endswith('.mp4')

    # 获取主显示器区域
    monitor = get_primary_monitor_geometry()
    print(f"录制区域: {monitor}", file=sys.stderr)
    print(f"使用 GNOME ScreencastArea 录制 {duration} 秒...", file=sys.stderr)

    # 连接 D-Bus session bus
    bus = dbus.SessionBus()

    # 获取 GNOME Shell Screencast 对象
    screencast_obj = bus.get_object(
        "org.gnome.Shell.Screencast",
        "/org/gnome/Shell/Screencast"
    )
    screencast = dbus.Interface(screencast_obj, "org.gnome.Shell.Screencast")

    # 构建录制选项
    options = {
        "draw-cursor": dbus.Boolean(capture_cursor),
        "framerate": dbus.Int32(framerate)
    }

    # 如果需要 mp4，使用 GStreamer pipeline 直接录制
    if is_mp4:
        # GNOME 40+ 需要 videoconvert 元素
        pipeline = (
            "videoconvert chroma-mode=none dither=none matrix-mode=output-only ! "
            "x264enc speed-preset=ultrafast qp-min=18 qp-max=28 ! "
            "queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! "
            "mp4mux"
        )
        options["pipeline"] = dbus.String(pipeline)

    # 使用 ScreencastArea 录制指定区域（主显示器）
    success, actual_file = screencast.ScreencastArea(
        dbus.Int32(monitor["x"]),
        dbus.Int32(monitor["y"]),
        dbus.Int32(monitor["width"]),
        dbus.Int32(monitor["height"]),
        str(output_path),
        options
    )

    if not success:
        raise RuntimeError("GNOME Screencast 启动失败")

    print(f"录制中... 文件: {actual_file}", file=sys.stderr)

    # 等待指定时长
    time.sleep(duration)

    # 停止录制
    screencast.StopScreencast()
    print(f"录制完成: {actual_file}", file=sys.stderr)

    actual_output = str(actual_file) if actual_file else str(output_path)

    # GNOME Screencast 使用 pipeline 时可能会添加错误后缀，需要重命名
    actual_path = Path(actual_output)
    if actual_path.exists() and actual_path.name != output_path.name:
        import shutil
        shutil.move(str(actual_path), str(output_path))
        actual_output = str(output_path)
        print(f"重命名为: {actual_output}", file=sys.stderr)

    return {
        "tool": "gnome-screencast-dbus",
        "format": "mp4" if is_mp4 else "webm",
        "file": actual_output
    }


def get_video_duration(file_path: str) -> float:
    """获取视频时长"""
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
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 检测显示服务器
        display_server = get_display_server()
        print(f"检测到显示服务器: {display_server}", file=sys.stderr)

        # 获取窗口几何信息
        if display_server == "x11":
            geometry = get_chrome_window_geometry_x11()
        else:
            geometry = get_chrome_window_geometry_wayland()

        print(f"窗口几何: {geometry}", file=sys.stderr)

        # 录制
        if display_server == "x11":
            record_info = record_screen_x11(
                output_file, duration, geometry, framerate, capture_cursor
            )
        else:
            record_info = record_screen_wayland(
                output_file, duration, geometry, framerate, capture_cursor
            )

        # 获取实际视频时长
        actual_duration = get_video_duration(output_file)
        file_size = output_path.stat().st_size if output_path.exists() else 0

        # 输出结果
        result = {
            "success": True,
            "file_path": str(output_path.absolute()),
            "duration": actual_duration,
            "file_size": file_size,
            "window_geometry": geometry,
            "display_server": display_server,
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
