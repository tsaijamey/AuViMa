#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Workflow: video_record_segment
Description: 录制单个视频段落，包括 CDP 操作、录屏和配音
Created: 2025-11-26
Version: 1.0.0
"""

import json
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Optional


def run_frago_command(command: str, args: list = None) -> dict:
    """执行 frago 命令"""
    cmd = ["uv", "run", "frago", command]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


def run_recipe(recipe_name: str, params: dict) -> dict:
    """执行 Recipe - 通过 frago recipe run 调用，自动处理 system_packages"""
    cmd = [
        "uv", "run", "frago", "recipe", "run",
        recipe_name,
        "--params", json.dumps(params)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode == 0:
        try:
            return {"success": True, "data": json.loads(result.stdout)}
        except json.JSONDecodeError:
            return {"success": True, "data": {"raw_output": result.stdout}}
    else:
        return {
            "success": False,
            "error": result.stderr or result.stdout
        }


def execute_cdp_action(action: dict) -> dict:
    """执行单个 CDP action"""
    action_type = action.get("action")
    wait_after = action.get("wait", 0)

    result = {"action": action_type, "success": False}

    try:
        if action_type == "navigate":
            url = action.get("url")
            res = run_frago_command("navigate", [url])
            result["success"] = res["success"]

        elif action_type == "click":
            selector = action.get("selector")
            res = run_frago_command("click", [selector])
            result["success"] = res["success"]

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            pixels = action.get("pixels", 500)
            scroll_value = pixels if direction == "down" else -pixels
            res = run_frago_command("scroll", [str(scroll_value)])
            result["success"] = res["success"]

        elif action_type == "highlight":
            selector = action.get("selector")
            res = run_frago_command("highlight", [selector])
            result["success"] = res["success"]

        elif action_type == "pointer":
            selector = action.get("selector")
            res = run_frago_command("pointer", [selector])
            result["success"] = res["success"]

        elif action_type == "wait":
            duration = action.get("duration", 1)
            time.sleep(duration)
            result["success"] = True

        elif action_type == "exec_js":
            expression = action.get("expression")
            res = run_frago_command("exec-js", [expression])
            result["success"] = res["success"]

        else:
            result["error"] = f"未知的 action 类型: {action_type}"

        # 操作后等待
        if wait_after > 0:
            time.sleep(wait_after)

    except Exception as e:
        result["error"] = str(e)

    return result


def record_with_actions(
    segment: dict,
    output_dir: Path
) -> dict:
    """执行 actions 并同时录制"""

    segment_id = segment.get("segment_id", "segment")
    duration = segment.get("duration", 10)
    actions = segment.get("actions", [])

    video_file = str(output_dir / f"{segment_id}.mp4")
    audio_file = str(output_dir / f"{segment_id}_audio.mp3")
    final_file = str(output_dir / f"{segment_id}_final.mp4")

    results = {
        "segment_id": segment_id,
        "actions_executed": [],
        "video_file": None,
        "audio_file": None,
        "final_file": None
    }

    # 1. 启动录制（在后台线程）
    record_result = {"success": False}
    record_error = None

    def do_record():
        nonlocal record_result, record_error
        try:
            record_result = run_recipe("video_browser_window_record", {
                "duration": duration,
                "output_file": video_file
            })
        except Exception as e:
            record_error = str(e)

    record_thread = threading.Thread(target=do_record)
    record_thread.start()

    # 2. 执行 actions（与录制并行）
    print(f"执行 {len(actions)} 个 actions...", file=sys.stderr)
    for action in actions:
        action_result = execute_cdp_action(action)
        results["actions_executed"].append(action_result)
        if not action_result.get("success"):
            print(f"  警告: action {action.get('action')} 失败", file=sys.stderr)

    # 3. 等待录制完成
    record_thread.join()

    if record_error:
        raise RuntimeError(f"录制失败: {record_error}")

    if not record_result.get("success"):
        raise RuntimeError(f"录制失败: {record_result.get('error')}")

    results["video_file"] = video_file

    # 4. 生成配音
    narration = segment.get("narration")
    if narration:
        audio_config = segment.get("audio_config", {})
        print(f"生成配音...", file=sys.stderr)

        audio_result = run_recipe("tts_generate_voice", {
            "text": narration,
            "output_file": audio_file,
            "voice": audio_config.get("voice", "zh-CN-YunxiNeural"),
            "speed": audio_config.get("speed", 1.0)
        })

        if not audio_result.get("success"):
            raise RuntimeError(f"配音生成失败: {audio_result.get('error')}")

        results["audio_file"] = audio_file

        # 5. 验证同步
        print(f"验证音视频同步...", file=sys.stderr)
        sync_result = run_recipe("video_validate_av_sync", {
            "video_file": video_file,
            "audio_file": audio_file
        })

        results["sync_check"] = sync_result.get("data", {})

        # 6. 合并音视频
        if sync_result.get("success"):
            print(f"合并音视频...", file=sys.stderr)
            merge_result = run_recipe("video_add_audio_track", {
                "video_file": video_file,
                "audio_file": audio_file,
                "output_file": final_file
            })

            if merge_result.get("success"):
                results["final_file"] = final_file
            else:
                print(f"  警告: 合并失败: {merge_result.get('error')}", file=sys.stderr)
        else:
            print(f"  警告: 音视频不同步，跳过合并", file=sys.stderr)
            results["sync_warning"] = sync_result.get("data", {}).get("suggestions", [])
    else:
        # 无配音，直接复制视频
        results["final_file"] = video_file

    return results


def main():
    """主函数"""
    # 解析参数
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
    segment = params.get("segment")
    output_dir = params.get("output_dir", "clips")

    if not segment:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: segment"
        }), file=sys.stderr)
        sys.exit(1)

    try:
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        segment_id = segment.get("segment_id", "segment")
        print(f"开始录制段落: {segment_id}", file=sys.stderr)

        # 执行录制
        results = record_with_actions(segment, output_path)

        # 输出结果
        output = {
            "success": True,
            **results
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
