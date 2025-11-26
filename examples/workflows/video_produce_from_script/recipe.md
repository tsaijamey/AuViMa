---
name: video_produce_from_script
type: workflow
runtime: python
description: "从视频脚本 JSON 文件自动生成完整视频，包括录屏、配音和合成（跨平台）"
use_cases:
  - "根据预定义脚本自动制作演示视频"
  - "批量生成教程或介绍视频"
  - "CI/CD 中的自动化视频生成"
tags:
  - video
  - workflow
  - automation
  - production
  - cross-platform
output_targets:
  - stdout
  - file
inputs:
  script_file:
    type: string
    required: false
    description: "视频脚本 JSON 文件路径（与 script 二选一）"
  script:
    type: object
    required: false
    description: "视频脚本对象（与 script_file 二选一）"
  output_dir:
    type: string
    required: false
    description: "输出目录，默认 'video_output'"
outputs:
  final_video:
    type: string
    description: "最终合成的视频文件路径"
  statistics:
    type: object
    description: "处理统计 {total_segments, processed, failed}"
  segments_processed:
    type: array
    description: "成功处理的段落列表"
  failed_segments:
    type: array
    description: "失败的段落列表"
dependencies:
  - video_record_segment
  - video_merge_clips
version: "1.1.0"
---

# video_produce_from_script

## 功能描述

从视频脚本自动生成完整视频的顶层 Workflow。解析 VideoScript JSON，逐个处理每个段落（调用 `video_record_segment`），最后合并所有片段为最终视频。

## 使用方法

```bash
# 从脚本文件生成
uv run frago recipe run video_produce_from_script \
  --params '{"script_file": "my_video_script.json", "output_dir": "output"}' \
  --output-file result.json

# 直接传入脚本对象
uv run frago recipe run video_produce_from_script \
  --params '{
    "script": {
      "script_id": "demo",
      "title": "演示视频",
      "segments": [...],
      "output_config": {"output_dir": "outputs", "final_filename": "demo.mp4"}
    }
  }'
```

## 视频脚本格式 (VideoScript JSON)

```json
{
  "script_id": "github_intro",
  "title": "GitHub 平台介绍",
  "description": "一个简短的 GitHub 介绍视频",
  "version": "1.0.0",
  "global_config": {
    "default_voice": "zh-CN-YunxiNeural",
    "default_resolution": "1280x960",
    "default_framerate": 30
  },
  "segments": [
    {
      "segment_id": "seg_001",
      "segment_type": "browser_recording",
      "duration": 10,
      "description": "展示 GitHub 首页",
      "actions": [
        {"action": "navigate", "url": "https://github.com", "wait": 3},
        {"action": "highlight", "selector": ".header-logo", "wait": 2}
      ],
      "narration": "GitHub 是全球最大的代码托管平台",
      "audio_config": {"voice": "zh-CN-YunxiNeural", "speed": 1.0}
    },
    {
      "segment_id": "seg_002",
      "segment_type": "browser_recording",
      "duration": 8,
      "description": "展示热门项目",
      "actions": [
        {"action": "navigate", "url": "https://github.com/trending", "wait": 3}
      ],
      "narration": "这里是当前最热门的开源项目"
    }
  ],
  "output_config": {
    "output_dir": "outputs/github_intro",
    "final_filename": "github_intro_final.mp4",
    "codec": "libx264"
  }
}
```

## 前置条件

- Chrome CDP 已连接
- ffmpeg 已安装
- **macOS**: 需要授权屏幕录制权限
- **Linux**: xdotool 已安装（X11 环境）
- 所有依赖 Recipe 可用

## 预期输出

```json
{
  "success": true,
  "script_id": "github_intro",
  "title": "GitHub 平台介绍",
  "output_dir": "/absolute/path/to/video_output",
  "final_video": "/absolute/path/to/outputs/github_intro/github_intro_final.mp4",
  "statistics": {
    "total_segments": 2,
    "processed": 2,
    "failed": 0
  },
  "segments_processed": [
    {"segment_id": "seg_001", "final_file": "clips/seg_001_final.mp4", "success": true},
    {"segment_id": "seg_002", "final_file": "clips/seg_002_final.mp4", "success": true}
  ],
  "failed_segments": []
}
```

## 执行流程

```
┌────────────────────┐
│ 解析视频脚本        │
│ (script_file/script)│
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 验证脚本格式        │
└─────────┬──────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 遍历所有 Segments                       │
│                                         │
│   ┌─────────────────────────────────┐  │
│   │ video_record_segment            │  │
│   │ (录制 + 配音 + 合成单个段落)     │  │
│   └─────────────────────────────────┘  │
│                                         │
│   重复直到所有段落处理完成              │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────┐
│ video_merge_clips  │
│ (合并所有片段)      │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 输出最终视频        │
└────────────────────┘
```

## 错误处理

- **单个段落失败**: 记录到 `failed_segments`，继续处理其他段落
- **合并失败**: 记录 `merge_error`，返回已处理的片段
- **全部失败**: `success: false`，提供详细错误信息

## 注意事项

- **跨平台支持**: 通过 `video_record_segment` 自动选择对应平台的录屏 Recipe
- **顺序执行**: 段落按顺序逐个处理，不支持并行（避免 CDP 冲突）
- **超时**: 每个段落超时 = duration + 120 秒
- **部分成功**: 即使部分段落失败，仍会尝试合并成功的段落

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.1.0 | 添加跨平台支持说明 |
| 2025-11-26 | v1.0.0 | 初始版本 |
