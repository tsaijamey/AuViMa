---
name: linux_video_screen_crop_record
type: atomic
runtime: python
description: "Linux 专用 - 屏幕区域录制（ffmpeg crop 方式，窗口被遮挡时无法正确录制）"
use_cases:
  - "CI/CD 无头环境的屏幕录制"
  - "无 OBS 环境时的备选方案"
  - "简单的屏幕区域录制 (X11/Wayland)"
tags:
  - video
  - screen-recording
  - ffmpeg
  - chrome
  - linux
  - x11
  - wayland
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
  window_geometry:
    type: object
    description: "录制窗口的几何信息 {x, y, width, height}"
dependencies: []
version: "1.1.0"
system_packages: true  # 需要系统 dbus 库
platform: linux
---

# linux_video_screen_crop_record

## 功能描述

Linux 专用的 **屏幕区域录制** Recipe，使用 ffmpeg 录制 Chrome 窗口所在的屏幕区域。

**注意**: 这是基于屏幕坐标的裁剪录制，如果 Chrome 窗口被其他窗口遮挡，会录到遮挡物。如需真正的窗口级录制，请使用 `obs_video_browser_window_record`。

自动检测显示服务器类型（X11/Wayland），定位 Chrome 窗口位置，使用 ffmpeg 进行屏幕录制。

支持的显示服务器：
- **X11**: 使用 xdotool 获取窗口位置，ffmpeg x11grab 录制
- **Wayland**: 使用 wf-recorder 或 pipewire 录制（需要额外配置）

## 使用方法

```bash
# 录制 10 秒视频
uv run frago recipe run video_browser_window_record \
  --params '{"duration": 10, "output_file": "output.mp4"}'

# 指定帧率和不录制光标
uv run frago recipe run video_browser_window_record \
  --params '{"duration": 15, "output_file": "demo.mp4", "framerate": 60, "capture_cursor": false}'
```

## 前置条件

- Chrome 浏览器已打开并可见
- ffmpeg 已安装
- X11 环境需要 xdotool (`sudo apt install xdotool`)
- Wayland 环境推荐安装 wf-recorder (`sudo apt install wf-recorder`)

## 预期输出

```json
{
  "success": true,
  "file_path": "/absolute/path/to/output.mp4",
  "duration": 10.05,
  "file_size": 1234567,
  "window_geometry": {
    "x": 100,
    "y": 50,
    "width": 1280,
    "height": 960
  },
  "display_server": "x11"
}
```

## 注意事项

- **Wayland 限制**: Wayland 下获取窗口位置较困难，可能使用默认值
- **权限**: 某些 Wayland 合成器需要额外权限才能录屏
- **性能**: 使用 `ultrafast` 预设以减少 CPU 占用，可能影响压缩率

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.1.0 | 重命名为 linux_ 前缀，标识为 Linux 专用版本 |
| 2025-11-26 | v1.0.0 | 初始版本，支持 X11 和 Wayland |
