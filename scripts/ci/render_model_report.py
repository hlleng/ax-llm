#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--workflow-run-url", required=True)
    parser.add_argument("--mode", required=True, choices=("smoke", "scan-updates"))
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def format_mib(value):
    return "-" if value is None else f"{value / 1024:.1f}"


def format_gib(value):
    return "-" if value is None else f"{value / 1024 ** 3:.2f}"


def format_available_memory(summary, name):
    after = summary.get("resources_after", {}).get(name)
    return format_mib(after)


def format_flash(summary):
    model_size = summary.get("model_size_bytes")
    free = summary.get("resources_after", {}).get("flash", {}).get("free")
    model = "-" if model_size is None else f"{model_size / 1024 ** 2:.1f} MiB"
    return f"模型 {model}; 可用 {format_gib(free)} GiB"


def escape(value):
    return str(value).replace("|", "\\|")


def create_header():
    return """# AX650 模型冒烟测试结果

该文件由 GitHub Actions 在模型冒烟测试成功后自动追加。每个表格记录一次成功验证，便于观察模型版本、性能和板端资源变化。

- CMM：`/proc/ax_proc/mem_cmm_info` 中的可用 CMM，单位 MiB，记录 `llm_smoke` 完成后的数值。
- DDR：`/proc/meminfo` 中的 `MemAvailable`，单位 MiB，记录 `llm_smoke` 完成后的数值。
- FLASH：模型目录实际文件大小，以及 `/mnt/ssd/llm_smoke` 所在文件系统在测试后的可用容量。
- CMM 和 DDR 是测试结束后的快照，不代表测试过程中的峰值占用。
"""


def main():
    args = parse_args()
    matrix = load_json(args.result_root / "matrix-summary.json")
    rows = []
    for result in matrix.get("models", []):
        summary_path = args.result_root / result["key"] / "summary.json"
        summary = load_json(summary_path) if summary_path.is_file() else result
        duration = summary.get("duration_seconds")
        duration_text = "-" if duration is None else f"{duration:.3f}"
        rows.append(
            "| {model} | `{revision}` | {input_type} | {cmm} | {ddr} | {flash} | {duration} | {status} |".format(
                model=escape(summary.get("model_id", result["model_id"])),
                revision=escape(summary.get("revision", result["revision"])),
                input_type=escape(summary.get("media", result["input"])),
                cmm=format_available_memory(summary, "cmm_remaining_kb"),
                ddr=format_available_memory(summary, "ddr_available_kb"),
                flash=format_flash(summary),
                duration=duration_text,
                status=escape(summary.get("status", result["status"])),
            )
        )

    if not rows:
        raise RuntimeError("测试结果中没有模型记录")
    if not args.report.exists():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(create_header(), encoding="utf-8")

    timestamp = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S %Z")
    section = "\n\n## {timestamp}\n\n- 模式：`{mode}`\n- 源码提交：`{sha}`\n- 工作流：{url}\n\n| 模型 | Revision | 输入 | CMM 可用 (MiB) | DDR 可用 (MiB) | FLASH | 耗时 (s) | 结果 |\n|---|---|---|---:|---:|---|---:|---|\n{rows}\n".format(
        timestamp=timestamp,
        mode=args.mode,
        sha=args.source_sha,
        url=args.workflow_run_url,
        rows="\n".join(rows),
    )
    with args.report.open("a", encoding="utf-8") as report:
        report.write(section)


if __name__ == "__main__":
    main()
