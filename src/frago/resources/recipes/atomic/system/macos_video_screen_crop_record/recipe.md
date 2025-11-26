---
name: macos_video_screen_crop_record
type: atomic
runtime: python
description: "macOS 专用 - 屏幕区域录制（ffmpeg crop 方式，窗口被遮挡时无法正确录制）"
use_cases:
  - "CI/CD 无头环境的屏幕录制"
  - "无 OBS 环境时的备选方案"
  - "简单的屏幕区域录制"
tags:
  - video
  - screen-recording
  - ffmpeg
  - avfoundation
  - macos
  - quartz
  - screen-crop
  - fallback
output_targets:
  - stdout
  - file
inputs:
  duration:
    type: number
    required: true
    description: "录制时长（秒）"
  output_file:
    type: string
    required: true
    description: "输出视频文件路径"
  framerate:
    type: number
    required: false
    description: "帧率，默认 30"
  capture_cursor:
    type: boolean
    required: false
    description: "是否录制鼠标光标，默认 true"
outputs:
  file_path:
    type: string
    description: "输出文件绝对路径"
  duration:
    type: number
    description: "实际录制时长（秒）"
  file_size:
    type: number
    description: "文件大小（字节）"
  resolution:
    type: object
    description: "视频分辨率 {width, height}"
  window_bounds:
    type: object
    description: "录制的窗口边界 {x, y, width, height, title}"
  codec:
    type: string
    description: "视频编码格式"
  bitrate:
    type: number
    description: "视频码率 (bps)"
dependencies:
  - pyobjc-framework-Quartz
version: "1.1.0"
platform: macos
---

# macos_video_screen_crop_record

## 功能描述

macOS 专用的 **屏幕区域录制** Recipe，使用 ffmpeg crop 滤镜录制 Chrome 窗口所在的屏幕区域。

**注意**: 这是基于屏幕坐标的裁剪录制，如果 Chrome 窗口被其他窗口遮挡，会录到遮挡物。如需真正的窗口级录制，请使用 `obs_video_browser_window_record`。

**技术实现**：
- 使用 `Quartz.CGWindowListCopyWindowInfo` 获取 Chrome 窗口精确位置和大小
- 使用 `ffmpeg -f avfoundation` 捕获屏幕 + `crop` 滤镜裁剪到窗口区域
- 自动检测屏幕设备索引
- 支持光标捕获开关
- 输出 H.264 编码的 MP4 视频

**与 Linux 版本的对比**：
| 特性 | macOS (本 Recipe) | Linux (linux_video_browser_window_record) |
|------|-------------------|-------------------------------------------|
| 窗口定位 | Quartz CGWindowListCopyWindowInfo | xdotool (X11) / D-Bus (Wayland) |
| 录制方式 | avfoundation + crop 滤镜 | x11grab / GNOME Screencast |
| 依赖 | ffmpeg + pyobjc-framework-Quartz | ffmpeg + xdotool / dbus |

## 使用方法

```bash
# 录制 10 秒视频
uv run frago recipe run macos_video_browser_window_record \
  --params '{"duration": 10, "output_file": "output.mp4"}'

# 指定帧率和不录制光标
uv run frago recipe run macos_video_browser_window_record \
  --params '{"duration": 15, "output_file": "demo.mp4", "framerate": 60, "capture_cursor": false}'
```

## 前置条件

- **macOS 系统**（Darwin）
- **Chrome 浏览器已打开**：窗口必须可见（非最小化）
- **ffmpeg 已安装**：`brew install ffmpeg`
- **屏幕录制权限**：首次运行时系统会请求屏幕录制权限
  - 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制 → 允许 Terminal/iTerm

## 预期输出

```json
{
  "success": true,
  "file_path": "/absolute/path/to/output.mp4",
  "duration": 10.05,
  "file_size": 1234567,
  "resolution": {
    "width": 1280,
    "height": 960
  },
  "codec": "h264",
  "bitrate": 2100000,
  "platform": "macos",
  "window_bounds": {
    "x": 20,
    "y": 25,
    "width": 1280,
    "height": 960,
    "title": "GitHub"
  },
  "record_info": {
    "command": "ffmpeg -y -f avfoundation ... -vf crop=1280:960:20:25 ...",
    "screen_device": "1",
    "crop_filter": "crop=1280:960:20:25"
  }
}
```

## 注意事项

- **窗口定位**：使用 Quartz API 精确获取 Chrome 窗口位置和大小
- **屏幕录制权限**：首次运行需要在系统偏好设置中授权
- **窗口可见性**：Chrome 窗口必须可见（非最小化、非被遮挡）
- **多 Chrome 窗口**：如有多个窗口，录制最前面的主窗口
- **性能**：使用 `ultrafast` 预设以减少 CPU 占用
- **分辨率**：输出分辨率等于 Chrome 窗口大小

## 已验证的命令

```bash
# 窗口录制命令（已测试通过）
ffmpeg -y -f avfoundation -framerate 30 -capture_cursor 1 -i "1:" \
  -vf "crop=1280:960:20:25" \
  -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p -t 3 output.mp4
```

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.1.0 | 实现窗口级别录制，使用 Quartz 获取窗口位置 + crop 滤镜 |
| 2025-11-26 | v1.0.0 | 初始版本，macOS 全屏录制 |
