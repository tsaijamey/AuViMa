---
name: tts_generate_voice
type: atomic
runtime: python
description: "使用 Edge TTS 生成高质量语音配音，支持多种中英文语音"
use_cases:
  - "为视频生成旁白配音"
  - "将文本转换为语音文件"
  - "批量生成多语言配音"
tags:
  - tts
  - audio
  - voice
  - edge-tts
output_targets:
  - stdout
  - file
inputs:
  text:
    type: string
    required: true
    description: "要转换为语音的文本"
  output_file:
    type: string
    required: true
    description: "输出音频文件路径（支持 mp3/wav）"
  voice:
    type: string
    required: false
    description: "语音模型，默认 zh-CN-YunxiNeural"
  speed:
    type: number
    required: false
    description: "语速倍率，1.0 为正常速度，1.2 加快 20%"
  pitch:
    type: string
    required: false
    description: "音调调整，如 +10Hz 或 -5Hz"
outputs:
  file_path:
    type: string
    description: "输出文件绝对路径"
  duration:
    type: number
    description: "音频时长（秒）"
  file_size:
    type: number
    description: "文件大小（字节）"
  voice:
    type: string
    description: "使用的语音模型"
dependencies: []
version: "1.0.0"
env:
  EDGE_TTS_PROXY:
    required: false
    description: "代理服务器地址（如需要）"
---

# tts_generate_voice

## 功能描述

使用 Microsoft Edge TTS 服务生成高质量语音配音。支持多种中文和英文语音模型，可调节语速和音调。

常用语音模型：
- **中文**: `zh-CN-YunxiNeural` (男), `zh-CN-XiaoxiaoNeural` (女), `zh-CN-YunjianNeural` (男)
- **英文**: `en-US-GuyNeural` (男), `en-US-JennyNeural` (女)

## 使用方法

```bash
# 基本用法
uv run frago recipe run tts_generate_voice \
  --params '{"text": "你好，欢迎使用 Frago", "output_file": "audio.mp3"}'

# 指定语音和语速
uv run frago recipe run tts_generate_voice \
  --params '{"text": "Hello World", "output_file": "hello.mp3", "voice": "en-US-GuyNeural", "speed": 1.2}'
```

## 前置条件

- 网络连接（Edge TTS 需要联网）
- ffprobe 已安装（用于获取音频时长）

## 预期输出

```json
{
  "success": true,
  "file_path": "/absolute/path/to/audio.mp3",
  "duration": 3.5,
  "file_size": 56789,
  "voice": "zh-CN-YunxiNeural",
  "rate": "+0%",
  "pitch": "+0Hz"
}
```

## 注意事项

- **依赖**: 使用 PEP 723 内联依赖，首次运行会自动安装 `edge-tts`
- **网络**: Edge TTS 服务需要网络连接，国内可能需要代理
- **限制**: 单次文本长度建议不超过 5000 字符

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本，使用 edge-tts |
