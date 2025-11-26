---
name: obs-window-recording
description: 使用 OBS Studio WebSocket API 进行真正的窗口级录制。当需要录制被遮挡或最小化的浏览器窗口时使用此 skill。支持 macOS 和 Linux 跨平台。
---

# OBS 窗口级录制专家

你是一个 OBS Studio 窗口录制专家，精通使用 OBS WebSocket API 实现真正的窗口级捕获（即使窗口被遮挡也能录制）。

## Instructions

### 核心优势

| 特性 | OBS 窗口录制 | ffmpeg crop 方案 |
|------|-------------|-----------------|
| 窗口被遮挡时 | 仍能录制窗口内容 | 录到遮挡物 |
| 窗口最小化时 | 仍能录制 | 无法录制 |
| 跨平台 | macOS/Linux/Windows | 需分别实现 |
| 性能 | GPU 加速 | 一般 |

### 前置条件

1. **OBS Studio ≥ 28.0.0**（自带 WebSocket 插件）
2. **启用 WebSocket Server**: Tools → WebSocket Server Settings → Enable
3. **默认端口**: 4455
4. **Python 依赖**: `obsws-python`, `pyobjc-framework-Quartz` (macOS)

### 技术架构

```
┌─────────────────────────────────────────────────────┐
│  Python Script                                       │
│                                                      │
│  1. Quartz API 获取窗口 ID                          │
│     ↓                                                │
│  2. OBS WebSocket 创建 screen_capture 源            │
│     (type=1 窗口模式, ScreenCaptureKit)             │
│     ↓                                                │
│  3. 调整窗口尺寸匹配画布比例                        │
│     ↓                                                │
│  4. 缩放源填满画布                                   │
│     ↓                                                │
│  5. StartRecord → 等待 → StopRecord                 │
└─────────────────────────────────────────────────────┘
```

---

## 关键 API 调用

### 1. 连接 OBS

```python
import obsws_python as obs

# 无密码连接
client = obs.ReqClient(host='localhost', port=4455, password='')

# 验证连接
version = client.get_version()
print(f'OBS {version.obs_version}, WebSocket {version.obs_web_socket_version}')
```

### 2. 获取窗口 ID (macOS)

```python
import Quartz

def get_chrome_window_id():
    """使用 Quartz API 获取 Chrome 窗口 ID"""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )

    for win in windows:
        owner = win.get('kCGWindowOwnerName', '')
        layer = win.get('kCGWindowLayer', -1)

        if 'Chrome' in owner and layer == 0:
            bounds = win.get('kCGWindowBounds', {})
            width = int(bounds.get('Width', 0))
            height = int(bounds.get('Height', 0))

            if width > 200 and height > 200:
                return {
                    'id': win.get('kCGWindowNumber'),
                    'title': win.get('kCGWindowName', ''),
                    'width': width,
                    'height': height,
                    'x': int(bounds.get('X', 0)),
                    'y': int(bounds.get('Y', 0))
                }

    raise RuntimeError("未找到 Chrome 窗口")
```

### 3. 创建窗口捕获源

```python
def create_window_capture(client, scene_name, source_name, window_id):
    """创建 ScreenCaptureKit 窗口捕获源"""
    try:
        # 创建新源
        result = client.create_input(
            scene_name,           # 场景名称
            source_name,          # 源名称
            'screen_capture',     # 使用 ScreenCaptureKit
            {
                'type': 1,        # 1 = 窗口模式
                'window': window_id,
                'show_cursor': True
            },
            True                  # 启用
        )
        return result.input_uuid
    except Exception as e:
        if 'already exists' in str(e).lower():
            # 更新现有源
            client.set_input_settings(source_name, {'window': window_id}, True)
            return None
        raise
```

**重要**: 使用 `screen_capture` 而非 `window_capture`
- `screen_capture` 使用 ScreenCaptureKit (macOS 12.3+)
- `type: 1` 表示窗口捕获模式
- 能录制被遮挡的窗口

### 4. 调整窗口尺寸匹配画布

```python
import subprocess

def resize_chrome_to_ratio(target_ratio, current_height=960):
    """调整 Chrome 窗口尺寸以匹配目标比例"""
    new_width = int(current_height * target_ratio)
    new_width = new_width - (new_width % 2)  # 确保偶数

    script = f'''
    tell application "Google Chrome"
        set bounds of front window to {{20, 25, {20 + new_width}, {25 + current_height}}}
    end tell
    '''
    subprocess.run(['osascript', '-e', script], check=True)
    return new_width, current_height
```

### 5. 缩放源填满画布

```python
def scale_source_to_canvas(client, scene_name, source_name, source_w, source_h, canvas_w, canvas_h):
    """缩放源以填满画布"""
    # 获取场景项 ID
    items = client.get_scene_item_list(scene_name)
    item_id = None
    for item in items.scene_items:
        if item['sourceName'] == source_name:
            item_id = item['sceneItemId']
            break

    if not item_id:
        raise RuntimeError(f"未找到源: {source_name}")

    # 计算缩放
    scale = canvas_w / source_w

    # 应用变换
    client.set_scene_item_transform(scene_name, item_id, {
        'scaleX': scale,
        'scaleY': scale,
        'positionX': 0,
        'positionY': 0
    })
```

### 6. 录制控制

```python
import time

def record_duration(client, duration_seconds, output_callback=None):
    """录制指定时长"""
    client.start_record()

    for remaining in range(int(duration_seconds), 0, -1):
        if output_callback:
            output_callback(f"录制中... {remaining}s")
        time.sleep(1)

    client.stop_record()
```

---

## 完整示例

```python
#!/usr/bin/env python3
"""OBS 窗口录制完整示例"""

import obsws_python as obs
import Quartz
import subprocess
import time

def main():
    # 1. 连接 OBS
    client = obs.ReqClient(host='localhost', port=4455, password='')
    print(f"已连接 OBS {client.get_version().obs_version}")

    # 2. 获取画布尺寸
    video = client.get_video_settings()
    canvas_w, canvas_h = video.base_width, video.base_height
    canvas_ratio = canvas_w / canvas_h
    print(f"画布: {canvas_w}x{canvas_h} (比例 {canvas_ratio:.4f})")

    # 3. 获取 Chrome 窗口
    chrome = get_chrome_window_id()
    print(f"Chrome: ID={chrome['id']}, {chrome['width']}x{chrome['height']}")

    # 4. 调整 Chrome 尺寸匹配画布比例
    new_w, new_h = resize_chrome_to_ratio(canvas_ratio, chrome['height'])
    print(f"调整后: {new_w}x{new_h}")

    # 5. 重新获取窗口 ID (尺寸变化后 ID 可能变化)
    time.sleep(0.5)
    chrome = get_chrome_window_id()

    # 6. 创建/更新窗口捕获源
    scene_name = '场景'
    source_name = 'ChromeCapture'
    create_window_capture(client, scene_name, source_name, chrome['id'])
    print(f"已创建源: {source_name}")

    # 7. 缩放源填满画布
    scale_source_to_canvas(client, scene_name, source_name,
                           new_w, new_h, canvas_w, canvas_h)
    print("已缩放源")

    # 8. 录制 5 秒
    print("开始录制...")
    record_duration(client, 5)
    print("录制完成!")

if __name__ == '__main__':
    main()
```

---

## 常见问题

### 1. WebSocket 连接失败

```bash
# 检查 OBS 是否运行
pgrep -x OBS

# 检查端口
lsof -i :4455 | grep LISTEN

# 自动启动 OBS
open -a "OBS" && sleep 5
```

### 2. 窗口捕获黑屏

- 确认 OBS 有屏幕录制权限: 系统偏好设置 → 隐私与安全性 → 屏幕录制
- 使用 `screen_capture` (ScreenCaptureKit) 而非 `window_capture`
- 设置 `type: 1` 表示窗口模式

### 3. 画布两侧有黑条

调整 Chrome 窗口尺寸匹配画布比例:
```python
canvas_ratio = canvas_w / canvas_h
new_width = int(window_height * canvas_ratio)
```

### 4. 录制文件位置

默认保存到 `~/Movies/`，文件名格式: `YYYY-MM-DD HH-MM-SS.mov`

可通过 OBS 设置更改: Settings → Output → Recording Path

---

## 与 ffmpeg crop 方案对比

| 场景 | OBS 方案 | ffmpeg crop 方案 |
|------|----------|-----------------|
| Chrome 在前台 | 推荐 | 可用 |
| Chrome 被遮挡 | 推荐 | 不可用 |
| Chrome 最小化 | 可用 | 不可用 |
| 无 OBS 环境 | 不可用 | 推荐 |
| CI/CD 无头环境 | 不推荐 | 推荐 |

**建议**:
- 本地开发/演示录制 → OBS 方案
- CI/CD 自动化 → ffmpeg crop 方案 (需确保窗口在前台)
