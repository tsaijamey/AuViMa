#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Workflow: video_produce_from_script
Description: 从视频脚本 JSON 文件自动生成完整视频
Created: 2025-11-26
Version: 1.0.0
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_recipe(recipe_name: str, params: dict, timeout: int = 600) -> dict:
    """执行 Recipe - 通过 frago recipe run 调用，自动处理 system_packages

    返回值直接使用 frago recipe run 的输出（已是 {success, data, ...} 格式）
    """
    cmd = [
        "uv", "run", "frago", "recipe", "run",
        recipe_name,
        "--params", json.dumps(params)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode == 0:
        try:
            # frago recipe run 输出已是 {success: true, data: {...}} 格式
            output = json.loads(result.stdout)
            # 直接返回内层的 data（实际结果）
            return {"success": True, "data": output.get("data", output)}
        except json.JSONDecodeError:
            return {"success": True, "data": {"raw_output": result.stdout}}
    else:
        return {
            "success": False,
            "error": result.stderr or result.stdout
        }


def parse_video_script(script_file: str) -> dict:
    """解析视频脚本文件"""
    script_path = Path(script_file)

    if not script_path.exists():
        raise FileNotFoundError(f"脚本文件不存在: {script_file}")

    content = script_path.read_text(encoding='utf-8')
    return json.loads(content)


def validate_script(script: dict) -> list:
    """验证脚本格式"""
    errors = []

    if not script.get("script_id"):
        errors.append("缺少 script_id")

    if not script.get("segments"):
        errors.append("缺少 segments")

    segments = script.get("segments", [])
    segment_ids = set()

    for i, seg in enumerate(segments):
        seg_id = seg.get("segment_id")
        if not seg_id:
            errors.append(f"段落 {i}: 缺少 segment_id")
        elif seg_id in segment_ids:
            errors.append(f"段落 {i}: segment_id '{seg_id}' 重复")
        segment_ids.add(seg_id)

        if not seg.get("duration") or seg.get("duration", 0) <= 0:
            errors.append(f"段落 {i}: duration 无效")

    return errors


def produce_video(script: dict, output_dir: Path) -> dict:
    """执行视频制作流程"""

    segments = script.get("segments", [])
    output_config = script.get("output_config", {})

    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "script_id": script.get("script_id"),
        "segments_processed": [],
        "failed_segments": [],
        "final_clips": []
    }

    # 1. 逐个处理段落
    print(f"开始处理 {len(segments)} 个段落...", file=sys.stderr)

    for i, segment in enumerate(segments):
        seg_id = segment.get("segment_id", f"seg_{i:03d}")
        print(f"\n[{i+1}/{len(segments)}] 处理段落: {seg_id}", file=sys.stderr)

        try:
            # 调用 video_record_segment workflow
            seg_result = run_recipe("video_record_segment", {
                "segment": segment,
                "output_dir": str(clips_dir)
            }, timeout=segment.get("duration", 60) + 120)

            if seg_result.get("success"):
                seg_data = seg_result.get("data", {})
                final_file = seg_data.get("final_file") or seg_data.get("video_file")

                if final_file and Path(final_file).exists():
                    results["segments_processed"].append({
                        "segment_id": seg_id,
                        "final_file": final_file,
                        "success": True
                    })
                    results["final_clips"].append(final_file)
                    print(f"  ✓ 完成: {final_file}", file=sys.stderr)
                else:
                    results["failed_segments"].append({
                        "segment_id": seg_id,
                        "error": "输出文件不存在"
                    })
                    print(f"  ✗ 失败: 输出文件不存在", file=sys.stderr)
            else:
                results["failed_segments"].append({
                    "segment_id": seg_id,
                    "error": seg_result.get("error", "Unknown error")
                })
                print(f"  ✗ 失败: {seg_result.get('error')}", file=sys.stderr)

        except Exception as e:
            results["failed_segments"].append({
                "segment_id": seg_id,
                "error": str(e)
            })
            print(f"  ✗ 异常: {e}", file=sys.stderr)

    # 2. 合并所有片段
    if len(results["final_clips"]) > 0:
        print(f"\n合并 {len(results['final_clips'])} 个视频片段...", file=sys.stderr)

        final_output_dir = output_config.get("output_dir", str(output_dir / "outputs"))
        final_filename = output_config.get("final_filename", f"{script.get('script_id', 'video')}_final.mp4")

        Path(final_output_dir).mkdir(parents=True, exist_ok=True)
        final_output_file = str(Path(final_output_dir) / final_filename)

        if len(results["final_clips"]) == 1:
            # 只有一个片段，直接复制
            import shutil
            shutil.copy2(results["final_clips"][0], final_output_file)
            results["final_video"] = final_output_file
            print(f"  ✓ 单片段复制完成: {final_output_file}", file=sys.stderr)
        else:
            # 多个片段，调用 video_merge_clips
            merge_result = run_recipe("video_merge_clips", {
                "clips": results["final_clips"],
                "output_file": final_output_file
            })

            if merge_result.get("success"):
                results["final_video"] = final_output_file
                results["merge_info"] = merge_result.get("data", {})
                print(f"  ✓ 合并完成: {final_output_file}", file=sys.stderr)
            else:
                results["merge_error"] = merge_result.get("error")
                print(f"  ✗ 合并失败: {merge_result.get('error')}", file=sys.stderr)

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

    # 获取参数
    script_file = params.get("script_file")
    script_data = params.get("script")  # 也支持直接传入脚本对象
    output_dir = params.get("output_dir", "video_output")

    if not script_file and not script_data:
        print(json.dumps({
            "success": False,
            "error": "缺少必需参数: script_file 或 script"
        }), file=sys.stderr)
        sys.exit(1)

    try:
        # 解析脚本
        if script_data:
            script = script_data
        else:
            print(f"解析脚本文件: {script_file}", file=sys.stderr)
            script = parse_video_script(script_file)

        # 验证脚本
        errors = validate_script(script)
        if errors:
            print(json.dumps({
                "success": False,
                "error": f"脚本验证失败: {errors}"
            }), file=sys.stderr)
            sys.exit(1)

        script_id = script.get("script_id", "video")
        print(f"脚本ID: {script_id}", file=sys.stderr)
        print(f"标题: {script.get('title', 'N/A')}", file=sys.stderr)
        print(f"段落数: {len(script.get('segments', []))}", file=sys.stderr)

        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 执行制作流程
        results = produce_video(script, output_path)

        # 计算统计信息
        total_segments = len(script.get("segments", []))
        processed_count = len(results.get("segments_processed", []))
        failed_count = len(results.get("failed_segments", []))

        # 输出结果
        output = {
            "success": failed_count == 0 and "final_video" in results,
            "script_id": script_id,
            "title": script.get("title"),
            "output_dir": str(output_path.absolute()),
            "final_video": results.get("final_video"),
            "statistics": {
                "total_segments": total_segments,
                "processed": processed_count,
                "failed": failed_count
            },
            "segments_processed": results.get("segments_processed", []),
            "failed_segments": results.get("failed_segments", [])
        }

        if results.get("merge_info"):
            output["merge_info"] = results["merge_info"]

        if results.get("merge_error"):
            output["merge_error"] = results["merge_error"]

        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0 if output["success"] else 1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
