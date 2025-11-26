---
name: uv_build_and_publish_to_pypi
type: atomic
runtime: python
description: "使用 uv 构建 Python 包并发布到 PyPI"
use_cases:
  - "发布新版本到 PyPI"
  - "CI/CD 流水线中自动发布"
  - "本地快速发布包更新"
tags:
  - packaging
  - pypi
  - uv
  - publish
output_targets:
  - stdout
  - file
inputs:
  project_dir:
    type: string
    required: false
    default: "."
    description: "项目目录路径（包含 pyproject.toml）"
  env_file:
    type: string
    required: false
    default: ".env"
    description: ".env 文件路径（相对于 project_dir）"
  token_key:
    type: string
    required: false
    default: "pypi_api_token"
    description: ".env 中 PyPI token 的键名"
  clean_dist:
    type: boolean
    required: false
    default: true
    description: "构建前是否清理 dist 目录"
outputs:
  success:
    type: boolean
    description: "是否成功"
  project_dir:
    type: string
    description: "项目目录路径"
  steps:
    type: array
    description: "执行步骤详情"
dependencies: []
version: "1.0.0"
---

# uv_build_and_publish_to_pypi

## 功能描述

使用 uv 工具链构建 Python 包（生成 wheel 和 sdist）并发布到 PyPI。自动从 `.env` 文件读取 PyPI API token，支持自定义项目目录和 token 键名。

## 使用方法

**使用 Recipe 系统**（推荐）：
```bash
# 在当前目录构建并发布
uv run frago recipe run uv_build_and_publish_to_pypi

# 指定项目目录
uv run frago recipe run uv_build_and_publish_to_pypi \
  --params '{"project_dir": "/path/to/project"}'

# 使用自定义 token 键名
uv run frago recipe run uv_build_and_publish_to_pypi \
  --params '{"token_key": "PYPI_TOKEN"}'

# 不清理 dist 目录（追加构建）
uv run frago recipe run uv_build_and_publish_to_pypi \
  --params '{"clean_dist": false}'
```

**直接执行**：
```bash
python examples/atomic/system/uv_build_and_publish_to_pypi.py '{"project_dir": "."}'
```

## 前置条件

- 项目目录包含有效的 `pyproject.toml`
- `.env` 文件中配置了 PyPI API token（默认键名 `pypi_api_token`）
- 已安装 `uv` 工具
- PyPI 账户已创建且 token 有效

## 预期输出

```json
{
  "success": true,
  "project_dir": "/home/user/project",
  "steps": [
    {
      "step": "clean_dist",
      "status": "success",
      "message": "Removed /home/user/project/dist"
    },
    {
      "step": "build",
      "status": "success",
      "files": ["project-1.0.0.tar.gz", "project-1.0.0-py3-none-any.whl"],
      "output": "Successfully built dist/project-1.0.0.tar.gz\nSuccessfully built dist/project-1.0.0-py3-none-any.whl"
    },
    {
      "step": "publish",
      "status": "success",
      "output": "Publishing 2 files to https://upload.pypi.org/legacy/"
    }
  ]
}
```

**版本已存在时**：
```json
{
  "success": true,
  "steps": [
    {
      "step": "publish",
      "status": "skipped",
      "message": "Version already exists on PyPI"
    }
  ]
}
```

## 注意事项

- **Token 安全**：不要将 `.env` 文件提交到版本控制，确保 `.gitignore` 包含 `.env`
- **版本号**：发布前确保 `pyproject.toml` 中的 `version` 已更新，PyPI 不允许覆盖已发布版本
- **构建清理**：默认会清理 `dist/` 目录，避免上传旧版本文件
- **Token 来源**：优先从 `.env` 读取，其次从环境变量读取

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-26 | v1.0.0 | 初始版本 |
