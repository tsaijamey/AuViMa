---
name: video_add_audio_track
type: atomic
runtime: python
description: "将音频轨道添加到视频文件，支持替换或混合原音轨"
use_cases:
  - "为无声视频添加配音"
  - "替换视频原有音轨"
  - "视频制作流水线中的音视频合成步骤"
tags:
  - video
  - audio
  - ffmpeg
  - mux
output_targets:
  - stdout
  - file
inputs:
  video_file:
    type: string
    required: true
    description: "输入视频文件路径"
  audio_file:
    type: string
    required: true
    description: "输入音频文件路径"
  output_file:
    type: string
    required: true
    description: "输出视频文件路径"
  replace_audio:
    type: boolean
    required: false
    description: "是否替换原音轨，默认 true"
outputs:
  file_path:
    type: string
    description: "输出文件绝对路径"
  duration:
    type: number
    description: "输出视频时长（秒）"
  file_size:
    type: number
    description: "文件大小（字节）"
  input_video_duration:
    type: number
    description: "输入视频时长"
  input_audio_duration:
    type: number
    description: "输入音频时长"
dependencies: []
version: "1.0.0"
---

# video_add_audio_track

## 功能描述

使用 ffmpeg 将音频轨道添加到视频文件。支持两种模式：
- **替换模式**（默认）：移除原音轨，使用新音频
- **混合模式**：保留原音轨，添加新音频轨

输出视频长度以最短的流为准（使用 `-shortest` 参数）。

## 使用方法

```bash
# 替换音轨
uv run frago recipe run video_add_audio_track \
  --params '{"video_file": "video.mp4", "audio_file": "voice.mp3", "output_file": "final.mp4"}'

# 混合音轨（保留原声）
uv run frago recipe run video_add_audio_track \
  --params '{"video_file": "video.mp4", "audio_file": "bgm.mp3", "output_file": "with_bgm.mp4", "replace_audio": false}'
```

## 前置条件

- ffmpeg 已安装
- 输入视频和音频文件存在且可读

## 预期输出

```json
{
  "success": true,
  "file_path": "/absolute/path/to/final.mp4",
  "duration": 30.5,
  "file_size": 5678901,
  "input_video_duration": 32.0,
  "input_audio_duration": 30.5,
  "replace_audio": true
}
```

## 注意事项

- **时长对齐**: 使用 `-shortest` 确保输出以最短流为准
- **音频编码**: 输出音频统一编码为 AAC
- **视频编码**: 视频使用 stream copy（无重编码）

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本 |
