---
name: video_validate_av_sync
type: atomic
runtime: python
description: "验证视频和音频文件的时长是否同步，确保配音不会被截断"
use_cases:
  - "视频制作前检查音视频时长匹配"
  - "批量验证多个视频片段的同步性"
  - "自动化流水线中的质量检查步骤"
tags:
  - video
  - audio
  - validation
  - sync
  - ffprobe
output_targets:
  - stdout
inputs:
  video_file:
    type: string
    required: true
    description: "视频文件路径"
  audio_file:
    type: string
    required: true
    description: "音频文件路径"
  tolerance:
    type: number
    required: false
    description: "时长差异容差（秒），默认 0.5"
outputs:
  video_duration:
    type: number
    description: "视频时长（秒）"
  audio_duration:
    type: number
    description: "音频时长（秒）"
  difference:
    type: number
    description: "时长差异（视频 - 音频，正数表示视频更长）"
  is_synced:
    type: boolean
    description: "是否同步（视频 >= 音频且差异在容差内）"
  suggestions:
    type: array
    description: "不同步时的调整建议"
dependencies: []
version: "1.0.0"
---

# video_validate_av_sync

## 功能描述

验证视频和音频文件的时长是否同步。同步条件：
1. 视频时长 >= 音频时长（确保配音不被截断）
2. 时长差异在容差范围内

不同步时会提供调整建议，并以非零退出码退出。

## 使用方法

```bash
# 基本验证
uv run frago recipe run video_validate_av_sync \
  --params '{"video_file": "video.mp4", "audio_file": "voice.mp3"}'

# 自定义容差
uv run frago recipe run video_validate_av_sync \
  --params '{"video_file": "video.mp4", "audio_file": "voice.mp3", "tolerance": 1.0}'
```

## 前置条件

- ffprobe 已安装（ffmpeg 套件的一部分）
- 输入文件存在且可读

## 预期输出

**同步时**:
```json
{
  "success": true,
  "video_duration": 30.5,
  "audio_duration": 28.2,
  "difference": 2.3,
  "is_synced": true,
  "tolerance": 0.5
}
```

**不同步时**:
```json
{
  "success": true,
  "video_duration": 25.0,
  "audio_duration": 30.5,
  "difference": -5.5,
  "is_synced": false,
  "tolerance": 0.5,
  "suggestions": [
    "视频时长不足，需要延长 5.50 秒",
    "建议：增加视频 duration 或加快音频语速"
  ]
}
```

## 注意事项

- **退出码**: 同步返回 0，不同步返回 1（便于脚本判断）
- **容差**: 默认 0.5 秒，可根据需求调整
- **视频优先**: 要求视频 >= 音频，因为配音被截断比视频多余更严重

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本 |
