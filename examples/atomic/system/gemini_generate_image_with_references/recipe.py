#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "google-genai>=1.0.0",
# ]
# ///
"""
Recipe: gemini_generate_image_with_references
Platform: Google Gemini API
Description: 使用 Gemini API 生成图片，支持文本提示和参考图片输入
Created: 2025-11-26
Version: 1.0.0
"""

import json
import mimetypes
import os
import sys
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types


def load_image_as_part(image_path: str) -> types.Part:
    """
    加载本地图片文件为 Gemini API Part 对象

    Args:
        image_path: 图片文件路径

    Returns:
        types.Part 对象
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    # 获取 MIME 类型
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        # 根据扩展名推断
        ext = path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

    # 读取并编码图片
    with open(path, 'rb') as f:
        image_data = f.read()

    return types.Part.from_bytes(data=image_data, mime_type=mime_type)


def generate_image(
    prompt: str,
    images: list[str] | None = None,
    output_dir: str = ".",
    output_prefix: str = "gemini_output",
    aspect_ratio: str = "9:16",
    image_size: str = "1K"
) -> dict:
    """
    使用 Gemini API 生成图片

    Args:
        prompt: 文本提示词
        images: 参考图片路径列表（最多3张）
        output_dir: 输出目录
        output_prefix: 输出文件名前缀
        aspect_ratio: 宽高比 (如 "9:16", "16:9", "1:1", "4:3", "3:4")
        image_size: 图片尺寸 ("1K", "2K")

    Returns:
        包含生成结果的字典
    """
    # 检查 API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": {
                "type": "ConfigError",
                "message": "未设置环境变量 GEMINI_API_KEY"
            }
        }

    # 验证图片数量
    if images and len(images) > 3:
        return {
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": f"最多支持3张参考图片，当前提供了 {len(images)} 张"
            }
        }

    try:
        # 初始化客户端
        client = genai.Client(api_key=api_key)

        # 构建内容部分
        parts = []

        # 添加参考图片（如果有）
        if images:
            for img_path in images:
                try:
                    img_part = load_image_as_part(img_path)
                    parts.append(img_part)
                except FileNotFoundError as e:
                    return {
                        "success": False,
                        "error": {
                            "type": "FileNotFoundError",
                            "message": str(e)
                        }
                    }

        # 添加文本提示
        parts.append(types.Part.from_text(text=prompt))

        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]

        # 配置生成参数
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            ),
        )

        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成时间戳用于文件命名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 调用 API 并处理响应
        generated_files = []
        text_responses = []
        file_index = 0

        for chunk in client.models.generate_content_stream(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            for part in chunk.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    # 保存图片
                    inline_data = part.inline_data
                    file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                    file_name = f"{output_prefix}_{timestamp}_{file_index}{file_extension}"
                    file_path = output_path / file_name

                    with open(file_path, "wb") as f:
                        f.write(inline_data.data)

                    generated_files.append({
                        "path": str(file_path.absolute()),
                        "filename": file_name,
                        "mime_type": inline_data.mime_type,
                        "size_bytes": len(inline_data.data)
                    })
                    file_index += 1
                elif part.text:
                    text_responses.append(part.text)

        if not generated_files:
            return {
                "success": False,
                "error": {
                    "type": "GenerationError",
                    "message": "API 未返回图片数据",
                    "text_response": "".join(text_responses) if text_responses else None
                }
            }

        return {
            "success": True,
            "prompt": prompt,
            "reference_images": images or [],
            "settings": {
                "aspect_ratio": aspect_ratio,
                "image_size": image_size
            },
            "generated_files": generated_files,
            "text_response": "".join(text_responses) if text_responses else None,
            "total_generated": len(generated_files)
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }


def main():
    """主函数：解析参数并执行图片生成"""

    # 解析输入参数
    if len(sys.argv) < 2:
        params = {}
    else:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "error": f"参数 JSON 解析失败: {e}"
            }), file=sys.stderr)
            sys.exit(1)

    # 验证必需参数
    prompt = params.get('prompt')
    if not prompt:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: prompt"
        }), file=sys.stderr)
        sys.exit(1)

    # 可选参数
    images = params.get('images', [])
    output_dir = params.get('output_dir', '.')
    output_prefix = params.get('output_prefix', 'gemini_output')
    aspect_ratio = params.get('aspect_ratio', '9:16')
    image_size = params.get('image_size', '1K')

    # 执行生成
    result = generate_image(
        prompt=prompt,
        images=images if images else None,
        output_dir=output_dir,
        output_prefix=output_prefix,
        aspect_ratio=aspect_ratio,
        image_size=image_size
    )

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 设置退出码
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
