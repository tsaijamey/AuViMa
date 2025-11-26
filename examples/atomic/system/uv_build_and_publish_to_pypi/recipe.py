#!/usr/bin/env python3
"""
Recipe: uv_build_and_publish_to_pypi
Description: 使用 uv 构建 Python 包并发布到 PyPI
Created: 2025-11-26
Version: 1.0.0
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def load_env_file(env_path: Path) -> dict:
    """加载 .env 文件"""
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def run_command(cmd: list, cwd: Path = None) -> tuple[int, str, str]:
    """执行命令并返回结果"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def main():
    # 解析输入参数
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            params = {}
    else:
        params = {}

    # 获取参数
    project_dir = Path(params.get('project_dir', '.')).resolve()
    env_file = params.get('env_file', '.env')
    token_key = params.get('token_key', 'pypi_api_token')
    clean_dist = params.get('clean_dist', True)

    # 验证项目目录
    pyproject_path = project_dir / 'pyproject.toml'
    if not pyproject_path.exists():
        print(json.dumps({
            "success": False,
            "error": f"pyproject.toml not found in {project_dir}"
        }, ensure_ascii=False))
        sys.exit(1)

    # 加载 .env 文件获取 token
    env_path = project_dir / env_file
    env_vars = load_env_file(env_path)

    token = env_vars.get(token_key) or os.environ.get(token_key)
    if not token:
        print(json.dumps({
            "success": False,
            "error": f"PyPI token not found. Set '{token_key}' in {env_file} or environment"
        }, ensure_ascii=False))
        sys.exit(1)

    results = {
        "project_dir": str(project_dir),
        "steps": []
    }

    # 步骤1: 清理 dist 目录（可选）
    if clean_dist:
        dist_dir = project_dir / 'dist'
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)
            results["steps"].append({
                "step": "clean_dist",
                "status": "success",
                "message": f"Removed {dist_dir}"
            })

    # 步骤2: 构建包
    print("Building package...", file=sys.stderr)
    returncode, stdout, stderr = run_command(['uv', 'build'], cwd=project_dir)

    if returncode != 0:
        print(json.dumps({
            "success": False,
            "error": f"Build failed: {stderr}",
            "steps": results["steps"]
        }, ensure_ascii=False))
        sys.exit(1)

    # 解析构建输出，获取生成的文件
    built_files = []
    for line in (stdout + stderr).split('\n'):
        if 'Successfully built' in line:
            # 提取文件名
            parts = line.replace('Successfully built', '').strip().split()
            built_files.extend(parts)

    results["steps"].append({
        "step": "build",
        "status": "success",
        "files": built_files,
        "output": stdout.strip()
    })

    # 步骤3: 发布到 PyPI
    print("Publishing to PyPI...", file=sys.stderr)
    returncode, stdout, stderr = run_command(
        ['uv', 'publish', '--token', token],
        cwd=project_dir
    )

    if returncode != 0:
        # 检查是否是版本已存在的错误
        if 'already exists' in stderr.lower() or 'file already exists' in stderr.lower():
            results["steps"].append({
                "step": "publish",
                "status": "skipped",
                "message": "Version already exists on PyPI",
                "output": stderr.strip()
            })
        else:
            print(json.dumps({
                "success": False,
                "error": f"Publish failed: {stderr}",
                "steps": results["steps"]
            }, ensure_ascii=False))
            sys.exit(1)
    else:
        results["steps"].append({
            "step": "publish",
            "status": "success",
            "output": stderr.strip() if stderr else stdout.strip()
        })

    # 输出结果
    output = {
        "success": True,
        **results
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
