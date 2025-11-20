"""Recipe 元数据解析和验证"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .exceptions import MetadataParseError, RecipeValidationError


@dataclass
class RecipeMetadata:
    """Recipe 元数据"""
    name: str
    type: str  # atomic | workflow
    runtime: str  # chrome-js | python | shell
    version: str
    description: str  # AI 可理解字段
    use_cases: list[str]  # AI 可理解字段
    output_targets: list[str]  # AI 可理解字段: stdout | file | clipboard
    inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # AI 可理解字段


def parse_metadata_file(path: Path) -> RecipeMetadata:
    """
    从 Markdown 文件的 YAML frontmatter 解析元数据
    
    Args:
        path: 元数据文件路径（.md 文件）
    
    Returns:
        RecipeMetadata 对象
    
    Raises:
        MetadataParseError: 解析失败时抛出
    """
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        raise MetadataParseError(str(path), f"无法读取文件: {e}")
    
    # 提取 YAML frontmatter
    if not content.startswith('---'):
        raise MetadataParseError(str(path), "文件不以 '---' 开头，缺少 YAML frontmatter")
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise MetadataParseError(str(path), "YAML frontmatter 格式错误，缺少结束的 '---'")
    
    yaml_content = parts[1].strip()
    
    # 解析 YAML
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise MetadataParseError(str(path), f"YAML 解析失败: {e}")
    
    if not isinstance(data, dict):
        raise MetadataParseError(str(path), "YAML frontmatter 必须是字典格式")
    
    # 构建 RecipeMetadata 对象
    try:
        metadata = RecipeMetadata(
            name=data['name'],
            type=data['type'],
            runtime=data['runtime'],
            version=data['version'],
            description=data['description'],
            use_cases=data['use_cases'],
            output_targets=data['output_targets'],
            inputs=data.get('inputs', {}),
            outputs=data.get('outputs', {}),
            dependencies=data.get('dependencies', []),
            tags=data.get('tags', []),
        )
    except KeyError as e:
        raise MetadataParseError(str(path), f"缺少必需字段: {e}")
    except Exception as e:
        raise MetadataParseError(str(path), f"元数据构建失败: {e}")
    
    return metadata


def validate_metadata(metadata: RecipeMetadata) -> None:
    """
    验证元数据的有效性
    
    Args:
        metadata: 要验证的元数据对象
    
    Raises:
        RecipeValidationError: 验证失败时抛出
    """
    errors = []
    
    # 验证 name
    if not metadata.name or not re.match(r'^[a-zA-Z0-9_-]+$', metadata.name):
        errors.append("name 必须仅包含字母、数字、下划线、连字符")
    
    # 验证 type
    if metadata.type not in ['atomic', 'workflow']:
        errors.append(f"type 必须是 'atomic' 或 'workflow'，当前值: '{metadata.type}'")
    
    # 验证 runtime
    if metadata.runtime not in ['chrome-js', 'python', 'shell']:
        errors.append(f"runtime 必须是 'chrome-js', 'python' 或 'shell'，当前值: '{metadata.runtime}'")
    
    # 验证 version
    if not re.match(r'^\d+\.\d+(\.\d+)?$', metadata.version):
        errors.append(f"version 格式无效: '{metadata.version}'，期望格式: '1.0' 或 '1.0.0'")
    
    # AI 字段验证
    if not metadata.description or len(metadata.description) > 200:
        errors.append("description 必须存在且长度 <= 200 字符")
    
    if not metadata.use_cases or len(metadata.use_cases) == 0:
        errors.append("use_cases 必须包含至少一个使用场景")
    
    if not metadata.output_targets or len(metadata.output_targets) == 0:
        errors.append("output_targets 必须包含至少一个输出目标")
    
    for target in metadata.output_targets:
        if target not in ['stdout', 'file', 'clipboard']:
            errors.append(f"output_targets 包含无效值: '{target}'，有效值: stdout, file, clipboard")
    
    # 验证 inputs
    for param_name, param_def in metadata.inputs.items():
        if 'type' not in param_def or 'required' not in param_def:
            errors.append(f"输入参数 '{param_name}' 缺少 'type' 或 'required' 字段")
    
    if errors:
        raise RecipeValidationError(metadata.name, errors)
