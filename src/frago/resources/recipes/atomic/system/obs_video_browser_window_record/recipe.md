---
name: obs_video_browser_window_record
type: atomic
runtime: python
description: "使用 OBS Studio WebSocket API 进行真正的窗口级录制（窗口被遮挡也能录制）"
use_cases:
  - "录制被其他窗口遮挡的 Chrome 浏览器"
  - "高质量视频演示录制（GPU 加速）"
  - "跨平台统一的窗口录制方案"
tags:
  - video
  - screen-recording
  - obs
  - websocket
  - window-capture
  - screencapturekit
  - cross-platform
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
    description: "输出视频文件路径（支持 .mp4 或 .mov）"
  scene_name:
    type: string
    required: false
    description: "OBS 场景名称，默认 '场景'"
  source_name:
    type: string
    required: false
    description: "窗口捕获源名称，默认 'ChromeCapture'"
  auto_start_obs:
    type: boolean
    required: false
    description: "OBS 未运行时自动启动，默认 true"
  adjust_window:
    type: boolean
    required: false
    description: "自动调整 Chrome 窗口尺寸匹配画布比例，默认 true"
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
    description: "录制的窗口信息 {id, title, width, height, x, y}"
  codec:
    type: string
    description: "视频编码格式"
  bitrate:
    type: number
    description: "视频码率 (bps)"
  method:
    type: string
    description: "录制方法标识 (obs_screencapturekit)"
dependencies:
  - obsws-python
  - pyobjc-framework-Quartz
version: "1.0.0"
platform: cross-platform
---

# obs_video_browser_window_record

## 功能描述

使用 **OBS Studio WebSocket API** 进行真正的窗口级录制。基于 ScreenCaptureKit 技术，即使 Chrome 窗口被其他窗口遮挡或最小化，也能正确录制窗口内容。

**核心优势**：

| 特性 | OBS 方案 (本 Recipe) | ffmpeg crop 方案 |
|------|---------------------|-----------------|
| 窗口被遮挡 | 仍能录制 | 录到遮挡物 |
| 窗口最小化 | 仍能录制 | 无法录制 |
| 跨平台 | macOS/Linux | 需分别实现 |
| 性能 | GPU 加速 | 一般 |

**技术实现**：
- 使用 `obsws-python` 连接 OBS WebSocket (端口 4455)
- 使用 `screen_capture` 源 (type=1 窗口模式) 实现 ScreenCaptureKit 窗口捕获
- 自动调整 Chrome 窗口尺寸匹配 OBS 画布比例
- 自动缩放源填满画布，消除黑边

## 使用方法

```bash
# 基础用法：录制 10 秒视频
uv run frago recipe run obs_video_browser_window_record \
  --params '{"duration": 10, "output_file": "output.mp4"}'

# 指定 OBS 场景和源名称
uv run frago recipe run obs_video_browser_window_record \
  --params '{
    "duration": 15,
    "output_file": "demo.mp4",
    "scene_name": "我的场景",
    "source_name": "BrowserWindow"
  }'

# 禁用自动窗口调整
uv run frago recipe run obs_video_browser_window_record \
  --params '{
    "duration": 10,
    "output_file": "output.mp4",
    "adjust_window": false
  }'
```

## 前置条件

1. **OBS Studio ≥ 28.0.0**：自带 WebSocket 插件
   - macOS: `brew install --cask obs`
   - Linux: `sudo apt install obs-studio`

2. **启用 WebSocket Server**：
   - OBS → Tools → WebSocket Server Settings
   - 勾选 "Enable WebSocket server"
   - 默认端口 4455，可无密码

3. **屏幕录制权限** (macOS)：
   - 系统偏好设置 → 隐私与安全性 → 屏幕录制 → 允许 OBS

4. **Chrome 浏览器已打开**：窗口必须存在（可被遮挡或最小化）

5. **xdotool** (Linux)：`sudo apt install xdotool`

## 预期输出

```json
{
  "success": true,
  "file_path": "/absolute/path/to/output.mp4",
  "duration": 10.05,
  "file_size": 2345678,
  "resolution": {
    "width": 3024,
    "height": 1964
  },
  "codec": "h264",
  "bitrate": 1800000,
  "platform": "darwin",
  "method": "obs_screencapturekit",
  "window_bounds": {
    "id": 49943,
    "title": "GitHub",
    "width": 1478,
    "height": 960,
    "x": 20,
    "y": 25
  },
  "record_info": {
    "obs_source": "ChromeCapture",
    "obs_scene": "场景",
    "canvas": {
      "width": 3024,
      "height": 1964
    }
  }
}
```

## 工作流程

```
┌─────────────────────────────────────────────────────┐
│ 1. 检查/启动 OBS                                    │
│    (auto_start_obs=true 时自动启动)                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. 获取 Chrome 窗口 ID                              │
│    macOS: Quartz.CGWindowListCopyWindowInfo         │
│    Linux: xdotool search --name Chrome              │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. 调整 Chrome 尺寸匹配画布比例                     │
│    (adjust_window=true 时执行)                      │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. 创建/更新 OBS 窗口捕获源                         │
│    screen_capture (type=1 窗口模式)                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. 缩放源填满画布                                   │
│    set_scene_item_transform(scaleX, scaleY)         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. StartRecord → 等待 duration → StopRecord         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 7. 转换格式 (mov → mp4) 并移动到 output_file        │
└─────────────────────────────────────────────────────┘
```

## 与其他录制 Recipe 的对比

| Recipe | 方法 | 窗口遮挡 | 平台 | 依赖 |
|--------|------|---------|------|------|
| **obs_video_browser_window_record** | OBS + ScreenCaptureKit | 可录 | 跨平台 | OBS Studio |
| macos_video_screen_crop_record | ffmpeg + crop | 不可 | macOS | ffmpeg |
| linux_video_screen_crop_record | ffmpeg + crop | 不可 | Linux | ffmpeg, xdotool |

**选择建议**：
- 本地开发/演示录制 → **本 Recipe (OBS 方案)**
- CI/CD 无头环境 → ffmpeg crop 方案
- 无 OBS 环境 → ffmpeg crop 方案

## 常见问题

### OBS WebSocket 连接失败
```bash
# 检查 OBS 是否运行
pgrep -x OBS  # macOS
pgrep -x obs  # Linux

# 检查端口监听
lsof -i :4455 | grep LISTEN

# 确认 WebSocket 已启用
# OBS → Tools → WebSocket Server Settings
```

### 录制画面黑屏
- 确认 OBS 有屏幕录制权限
- 使用 `screen_capture` 源而非 `window_capture`

### 画布两侧有黑条
设置 `adjust_window: true`（默认）自动调整 Chrome 尺寸匹配画布比例

### 录制文件位置
OBS 默认保存到 `~/Movies/`，本 Recipe 会自动移动到 `output_file` 指定位置

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本，基于 OBS WebSocket + ScreenCaptureKit |
