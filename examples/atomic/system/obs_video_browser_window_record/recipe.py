#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["obsws-python", "pyobjc-framework-Quartz"]
# ///
"""
Recipe: obs_video_browser_window_record
Description: 使用 OBS Studio WebSocket API 进行真正的窗口级录制（窗口被遮挡也能录制）
Created: 2025-11-26
Version: 1.0.0
"""

import json
import subprocess
import sys
import time
import platform
from pathlib import Path


def check_platform():
    """检查平台支持"""
    system = platform.system()
    if system not in ("Darwin", "Linux"):
        raise RuntimeError(f"不支持的平台: {system}，仅支持 macOS 和 Linux")
    return system


def check_obs_running():
    """检查 OBS 是否运行"""
    try:
        if platform.system() == "Darwin":
            result = subprocess.run(["pgrep", "-x", "OBS"], capture_output=True)
        else:
            result = subprocess.run(["pgrep", "-x", "obs"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def start_obs():
    """启动 OBS"""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-a", "OBS"], check=True)
    else:
        subprocess.Popen(["obs", "--minimize-to-tray"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)

    # 等待 OBS 启动和 WebSocket 就绪
    print("等待 OBS 启动...", file=sys.stderr)
    for i in range(30):
        time.sleep(1)
        try:
            import obsws_python as obs
            client = obs.ReqClient(host='localhost', port=4455, password='', timeout=2)
            client.get_version()
            print("OBS 已就绪", file=sys.stderr)
            return True
        except Exception:
            continue

    raise RuntimeError("OBS 启动超时")


def get_chrome_window_id_macos() -> dict:
    """macOS: 使用 Quartz 获取 Chrome 窗口信息"""
    import Quartz

    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )

    for win in windows:
        owner = win.get('kCGWindowOwnerName', '')
        layer = win.get('kCGWindowLayer', -1)

        if ('Chrome' in owner or 'Google Chrome' in owner) and layer == 0:
            bounds = win.get('kCGWindowBounds', {})
            width = int(bounds.get('Width', 0))
            height = int(bounds.get('Height', 0))

            if width > 200 and height > 200:
                return {
                    'id': win.get('kCGWindowNumber'),
                    'title': win.get('kCGWindowName', 'Unknown'),
                    'width': width,
                    'height': height,
                    'x': int(bounds.get('X', 0)),
                    'y': int(bounds.get('Y', 0))
                }

    raise RuntimeError("未找到 Chrome 浏览器窗口，请确保 Chrome 已打开")


def get_chrome_window_id_linux() -> dict:
    """Linux: 使用 xdotool 获取 Chrome 窗口信息"""
    try:
        # 获取窗口 ID
        result = subprocess.run(
            ["xdotool", "search", "--name", "Chrome"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise RuntimeError("未找到 Chrome 窗口")

        window_id = result.stdout.strip().split('\n')[0]

        # 获取窗口几何信息
        result = subprocess.run(
            ["xdotool", "getwindowgeometry", window_id],
            capture_output=True, text=True, timeout=5
        )

        # 解析输出
        import re
        pos_match = re.search(r'Position: (\d+),(\d+)', result.stdout)
        size_match = re.search(r'Geometry: (\d+)x(\d+)', result.stdout)

        if pos_match and size_match:
            return {
                'id': int(window_id),
                'title': 'Chrome',
                'width': int(size_match.group(1)),
                'height': int(size_match.group(2)),
                'x': int(pos_match.group(1)),
                'y': int(pos_match.group(2))
            }

        raise RuntimeError("无法解析窗口信息")
    except FileNotFoundError:
        raise RuntimeError("xdotool 未安装，请运行: sudo apt install xdotool")


def get_chrome_window_id() -> dict:
    """获取 Chrome 窗口信息（跨平台）"""
    if platform.system() == "Darwin":
        return get_chrome_window_id_macos()
    else:
        return get_chrome_window_id_linux()


def resize_chrome_window(target_ratio: float, height: int = 960) -> tuple:
    """调整 Chrome 窗口尺寸以匹配目标比例"""
    new_width = int(height * target_ratio)
    new_width = new_width - (new_width % 2)  # 确保偶数

    if platform.system() == "Darwin":
        script = f'''
        tell application "Google Chrome"
            set bounds of front window to {{20, 25, {20 + new_width}, {25 + height}}}
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
    else:
        # Linux: 使用 xdotool
        subprocess.run([
            "xdotool", "search", "--name", "Chrome",
            "windowsize", str(new_width), str(height)
        ], check=True, capture_output=True)

    return new_width, height


def record_with_obs(
    output_file: str,
    duration: float,
    scene_name: str = "场景",
    source_name: str = "ChromeCapture",
    auto_start_obs: bool = True,
    adjust_window: bool = True
) -> dict:
    """使用 OBS WebSocket 录制 Chrome 窗口"""
    import obsws_python as obs

    # 检查/启动 OBS
    if not check_obs_running():
        if auto_start_obs:
            start_obs()
        else:
            raise RuntimeError("OBS 未运行，请先启动 OBS 或设置 auto_start_obs=True")

    # 连接 OBS
    client = obs.ReqClient(host='localhost', port=4455, password='', timeout=10)
    version = client.get_version()
    print(f"OBS {version.obs_version}, WebSocket {version.obs_web_socket_version}", file=sys.stderr)

    # 获取画布尺寸
    video = client.get_video_settings()
    canvas_w, canvas_h = video.base_width, video.base_height
    canvas_ratio = canvas_w / canvas_h
    print(f"画布: {canvas_w}x{canvas_h}", file=sys.stderr)

    # 获取 Chrome 窗口
    chrome = get_chrome_window_id()
    print(f"Chrome: {chrome['width']}x{chrome['height']}, ID={chrome['id']}", file=sys.stderr)

    # 调整 Chrome 尺寸匹配画布比例
    if adjust_window:
        chrome_ratio = chrome['width'] / chrome['height']
        if abs(chrome_ratio - canvas_ratio) > 0.01:
            print(f"调整 Chrome 尺寸匹配画布比例...", file=sys.stderr)
            new_w, new_h = resize_chrome_window(canvas_ratio, chrome['height'])
            time.sleep(0.5)
            chrome = get_chrome_window_id()
            print(f"调整后: {chrome['width']}x{chrome['height']}", file=sys.stderr)

    # 创建/更新窗口捕获源
    try:
        client.create_input(
            scene_name,
            source_name,
            'screen_capture',  # 使用 ScreenCaptureKit
            {
                'type': 1,  # 窗口模式
                'window': chrome['id'],
                'show_cursor': True
            },
            True
        )
        print(f"已创建源: {source_name}", file=sys.stderr)
    except Exception as e:
        if 'already exists' in str(e).lower():
            client.set_input_settings(source_name, {'window': chrome['id']}, True)
            print(f"已更新源: {source_name}", file=sys.stderr)
        else:
            raise

    # 缩放源填满画布
    items = client.get_scene_item_list(scene_name)
    for item in items.scene_items:
        if item['sourceName'] == source_name:
            scale = canvas_w / chrome['width']
            client.set_scene_item_transform(scene_name, item['sceneItemId'], {
                'scaleX': scale,
                'scaleY': scale,
                'positionX': 0,
                'positionY': 0
            })
            print(f"缩放: {scale:.4f}", file=sys.stderr)
            break

    # 开始录制
    print(f"开始录制 {duration} 秒...", file=sys.stderr)
    client.start_record()

    start_time = time.time()
    while time.time() - start_time < duration:
        remaining = duration - (time.time() - start_time)
        print(f"  剩余 {remaining:.1f} 秒...", file=sys.stderr)
        time.sleep(min(1, remaining))

    client.stop_record()
    print("录制完成!", file=sys.stderr)

    # 等待文件写入
    time.sleep(1)

    # 查找最新录制文件
    movies_dir = Path.home() / "Movies"
    latest_file = max(movies_dir.glob("*.mov"), key=lambda p: p.stat().st_mtime, default=None)

    if latest_file and output_file:
        # 移动到指定位置
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果需要转换格式 (mov -> mp4)
        if output_path.suffix.lower() == '.mp4':
            subprocess.run([
                'ffmpeg', '-y', '-i', str(latest_file),
                '-c:v', 'copy', '-c:a', 'aac',
                str(output_path)
            ], capture_output=True, check=True)
            latest_file.unlink()  # 删除原文件
        else:
            latest_file.rename(output_path)

        return {
            'recorded_file': str(latest_file),
            'output_file': str(output_path.absolute()),
            'canvas': {'width': canvas_w, 'height': canvas_h},
            'window': chrome
        }

    return {
        'recorded_file': str(latest_file) if latest_file else None,
        'output_file': output_file,
        'canvas': {'width': canvas_w, 'height': canvas_h},
        'window': chrome
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
    scene_name = params.get("scene_name", "场景")
    source_name = params.get("source_name", "ChromeCapture")
    auto_start_obs = params.get("auto_start_obs", True)
    adjust_window = params.get("adjust_window", True)

    try:
        # 检查平台
        system = check_platform()

        # 录制
        record_info = record_with_obs(
            output_file=output_file,
            duration=duration,
            scene_name=scene_name,
            source_name=source_name,
            auto_start_obs=auto_start_obs,
            adjust_window=adjust_window
        )

        # 获取视频信息
        output_path = Path(output_file).absolute()
        video_info = get_video_info(str(output_path))

        # 输出结果
        result = {
            "success": True,
            "file_path": str(output_path),
            "duration": video_info.get("duration", 0),
            "file_size": video_info.get("file_size", 0),
            "resolution": {
                "width": video_info.get("width", 0),
                "height": video_info.get("height", 0)
            },
            "codec": video_info.get("codec", "unknown"),
            "bitrate": video_info.get("bitrate", 0),
            "platform": system.lower(),
            "method": "obs_screencapturekit",
            "window_bounds": record_info.get("window"),
            "record_info": {
                "obs_source": source_name,
                "obs_scene": scene_name,
                "canvas": record_info.get("canvas")
            }
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
