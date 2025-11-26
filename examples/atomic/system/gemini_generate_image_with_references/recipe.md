---
name: gemini_generate_image_with_references
type: atomic
runtime: python
description: "使用 Google Gemini API 生成图片，支持文本提示词和最多3张参考图片输入"
use_cases:
  - "根据文字描述生成创意图片"
  - "基于参考图片进行风格迁移或变体生成"
  - "图片编辑和扩展（提供原图+指令）"
  - "多图融合创作"
tags:
  - image-generation
  - gemini
  - ai-art
  - google-api
output_targets:
  - stdout
  - file
inputs:
  prompt:
    type: string
    required: true
    description: "图片生成的文本提示词"
  images:
    type: array
    required: false
    description: "参考图片路径列表（最多3张），支持 jpg/png/gif/webp/bmp 格式"
  output_dir:
    type: string
    required: false
    default: "."
    description: "输出目录路径"
  output_prefix:
    type: string
    required: false
    default: "gemini_output"
    description: "输出文件名前缀"
  aspect_ratio:
    type: string
    required: false
    default: "9:16"
    description: "图片宽高比（可选: 9:16, 16:9, 1:1, 4:3, 3:4）"
  image_size:
    type: string
    required: false
    default: "1K"
    description: "图片尺寸（可选: 1K, 2K）"
outputs:
  success:
    type: boolean
    description: "是否成功执行"
  prompt:
    type: string
    description: "使用的提示词"
  reference_images:
    type: array
    description: "使用的参考图片路径列表"
  settings:
    type: object
    description: "生成设置（aspect_ratio, image_size）"
  generated_files:
    type: array
    description: "生成的图片文件信息列表，每项包含 path, filename, mime_type, size_bytes"
  text_response:
    type: string
    description: "API 返回的文本响应（如果有）"
  total_generated:
    type: number
    description: "生成的图片数量"
dependencies: []
env_vars:
  GEMINI_API_KEY:
    required: true
    description: "Google Gemini API 密钥"
version: "1.0.0"
---

# gemini_generate_image_with_references

## 功能描述

使用 Google Gemini API（gemini-3-pro-image-preview 模型）生成图片。支持纯文本生成，也支持同时提供最多3张参考图片进行风格迁移、图片编辑或多图融合创作。

**核心特性**：
- ✅ **多模态输入**：文本 + 最多3张参考图片
- ✅ **灵活输出**：支持多种宽高比和尺寸
- ✅ **流式处理**：支持生成多张图片
- ✅ **JSON 输出**：结构化结果便于自动化处理

## 使用方法

**推荐方式**（Recipe 系统）：
```bash
# 纯文本生成
uv run frago recipe run gemini_generate_image_with_references \
  --params '{"prompt": "一只可爱的橘猫在阳光下打盹"}' \
  --output-file result.json

# 带参考图片生成
uv run frago recipe run gemini_generate_image_with_references \
  --params '{
    "prompt": "将这张照片转换为水彩画风格",
    "images": ["/path/to/photo.jpg"],
    "aspect_ratio": "16:9",
    "output_dir": "./output"
  }' \
  --output-file result.json

# 多图融合
uv run frago recipe run gemini_generate_image_with_references \
  --params '{
    "prompt": "融合这两张图片的风格，创造一个新场景",
    "images": ["/path/to/style.jpg", "/path/to/content.jpg"],
    "output_prefix": "fusion"
  }'
```

**传统方式**（直接执行）：
```bash
# 设置 API Key
export GEMINI_API_KEY="your-api-key"

# 执行脚本
uv run python examples/atomic/system/gemini_generate_image_with_references.py \
  '{"prompt": "未来城市的天际线", "aspect_ratio": "16:9"}'
```

## 前置条件

- Python 3.9+
- uv（用于自动管理 Recipe 依赖）
- 环境变量 `GEMINI_API_KEY` 已设置
- 网络连接（访问 Google Gemini API）

**依赖管理**：此 Recipe 使用 PEP 723 内联依赖声明，`uv run` 会自动在隔离环境中安装 `google-genai`，无需手动安装。

## 预期输出

```json
{
  "success": true,
  "prompt": "一只可爱的橘猫在阳光下打盹",
  "reference_images": [],
  "settings": {
    "aspect_ratio": "9:16",
    "image_size": "1K"
  },
  "generated_files": [
    {
      "path": "/absolute/path/to/gemini_output_20251126_143052_0.png",
      "filename": "gemini_output_20251126_143052_0.png",
      "mime_type": "image/png",
      "size_bytes": 1234567
    }
  ],
  "text_response": null,
  "total_generated": 1
}
```

**字段说明**：
- `generated_files[].path`: 生成图片的绝对路径
- `generated_files[].filename`: 文件名（格式: `{prefix}_{timestamp}_{index}.{ext}`）
- `generated_files[].mime_type`: MIME 类型
- `generated_files[].size_bytes`: 文件大小（字节）
- `text_response`: API 可能返回的文本说明

## 注意事项

- **API 配额**：Gemini API 有调用频率限制，请注意控制请求频率
- **图片格式**：支持 jpg, jpeg, png, gif, webp, bmp 格式的参考图片
- **图片数量**：最多支持3张参考图片，超出会返回错误
- **宽高比选项**：`9:16`（竖版）、`16:9`（横版）、`1:1`（方形）、`4:3`、`3:4`
- **尺寸选项**：`1K`（约1024px）、`2K`（约2048px）
- **输出目录**：如果指定的目录不存在，会自动创建
- **文件命名**：自动添加时间戳避免覆盖，格式为 `{prefix}_{YYYYMMDD_HHMMSS}_{index}.{ext}`

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本，支持文本+图片多模态输入 |
