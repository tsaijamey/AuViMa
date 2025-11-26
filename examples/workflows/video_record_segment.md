---
name: video_record_segment
type: workflow
runtime: python
description: "录制单个视频段落，包括 CDP 操作序列、浏览器窗口录屏和 TTS 配音生成"
use_cases:
  - "录制演示视频的单个场景"
  - "作为 video_produce_from_script 的子任务"
  - "自动化视频内容制作"
tags:
  - video
  - workflow
  - recording
  - tts
  - cdp
output_targets:
  - stdout
  - file
inputs:
  segment:
    type: object
    required: true
    description: "段落定义对象，包含 segment_id, duration, actions, narration 等"
  output_dir:
    type: string
    required: false
    description: "输出目录，默认 'clips'"
outputs:
  segment_id:
    type: string
    description: "段落 ID"
  video_file:
    type: string
    description: "录制的视频文件路径"
  audio_file:
    type: string
    description: "生成的配音文件路径"
  final_file:
    type: string
    description: "合并后的最终视频路径"
  actions_executed:
    type: array
    description: "执行的 actions 及其结果"
dependencies:
  - video_browser_window_record
  - tts_generate_voice
  - video_validate_av_sync
  - video_add_audio_track
version: "1.0.0"
system_packages: true  # 依赖 video_browser_window_record 需要系统 dbus
---

# video_record_segment

## 功能描述

录制单个视频段落的完整 Workflow，包括：

1. **准备阶段**: 解析段落配置
2. **录制阶段**: 同时启动屏幕录制和执行 CDP 操作
3. **配音阶段**: 使用 TTS 生成配音（如果有 narration）
4. **验证阶段**: 检查音视频时长同步
5. **合成阶段**: 将音频轨道添加到视频

## 使用方法

```bash
# 录制单个段落
uv run frago recipe run video_record_segment \
  --params '{
    "segment": {
      "segment_id": "intro_001",
      "duration": 10,
      "actions": [
        {"action": "navigate", "url": "https://github.com", "wait": 3},
        {"action": "highlight", "selector": ".header-logo", "wait": 2}
      ],
      "narration": "GitHub 是全球最大的代码托管平台",
      "audio_config": {"voice": "zh-CN-YunxiNeural", "speed": 1.0}
    },
    "output_dir": "clips"
  }'
```

## Segment 对象格式

```json
{
  "segment_id": "unique_id",
  "duration": 10,
  "segment_type": "browser_recording",
  "description": "段落描述",
  "actions": [
    {"action": "navigate", "url": "https://...", "wait": 3},
    {"action": "highlight", "selector": ".element", "color": "#FFD700", "wait": 2},
    {"action": "scroll", "direction": "down", "pixels": 500, "wait": 2}
  ],
  "narration": "配音文本...",
  "audio_config": {
    "voice": "zh-CN-YunxiNeural",
    "speed": 1.0
  }
}
```

## 支持的 Actions

| Action | 参数 | 说明 |
|--------|------|------|
| `navigate` | `url`, `wait` | 导航到 URL |
| `click` | `selector`, `wait` | 点击元素 |
| `scroll` | `direction`, `pixels`, `wait` | 滚动页面 |
| `highlight` | `selector`, `wait` | 高亮元素 |
| `pointer` | `selector`, `wait` | 显示指针 |
| `wait` | `duration` | 等待指定秒数 |
| `exec_js` | `expression`, `wait` | 执行 JavaScript |

## 前置条件

- Chrome CDP 已连接 (`uv run frago navigate` 可用)
- ffmpeg 已安装
- xdotool 已安装（X11 环境）

## 预期输出

```json
{
  "success": true,
  "segment_id": "intro_001",
  "video_file": "clips/intro_001.mp4",
  "audio_file": "clips/intro_001_audio.mp3",
  "final_file": "clips/intro_001_final.mp4",
  "actions_executed": [
    {"action": "navigate", "success": true},
    {"action": "highlight", "success": true}
  ],
  "sync_check": {
    "video_duration": 10.5,
    "audio_duration": 8.2,
    "is_synced": true
  }
}
```

## 执行流程

```
┌─────────────┐
│ 解析 Segment │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│       并行执行                         │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ 屏幕录制    │  │ CDP Actions │   │
│  │ (duration)  │  │ (顺序执行)   │   │
│  └─────────────┘  └─────────────┘   │
└──────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ TTS 配音    │ (如果有 narration)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 验证同步    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 合并音视频  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 输出结果    │
└─────────────┘
```

## 注意事项

- **录制与操作并行**: 录制在后台线程执行，同时执行 CDP actions
- **时长控制**: `duration` 字段控制录制时长，actions 应在此时间内完成
- **同步验证**: 如果音频比视频长，会记录警告但不会阻止执行

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本 |
