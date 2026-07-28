#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-root", required=True, type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--prompt", default="请用一个词回答：测试。")
    parser.add_argument("--dynamic-load-pool", type=int, default=0)
    media = parser.add_mutually_exclusive_group()
    media.add_argument("--image", type=Path)
    media.add_argument("--video", type=Path)
    media.add_argument("--audio", type=Path)
    return parser.parse_args()


def require_file(model_dir, value, field):
    path = Path(value)
    if not path.is_absolute():
        path = model_dir / path
    if not path.is_file():
        raise RuntimeError(f"配置字段 {field} 指向的文件不存在: {path}")


def verify_model_files(model_dir):
    config_path = model_dir / "config.json"
    if not config_path.is_file():
        raise RuntimeError(f"缺少模型配置: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    required_fields = (
        "template_filename_axmodel",
        "filename_post_axmodel",
        "url_tokenizer_model",
        "filename_tokens_embed",
        "post_config_path",
        "axmodel_num",
    )
    for field in required_fields:
        if field not in config:
            raise RuntimeError(f"config.json 缺少必填字段: {field}")

    for field in (
        "filename_post_axmodel",
        "url_tokenizer_model",
        "filename_tokens_embed",
        "post_config_path",
    ):
        require_file(model_dir, config[field], field)

    model_count = config["axmodel_num"]
    if not isinstance(model_count, int) or model_count <= 0:
        raise RuntimeError("config.json 的 axmodel_num 必须为正整数")
    template = config["template_filename_axmodel"]
    if "%d" not in template:
        raise RuntimeError("template_filename_axmodel 必须包含 %d")
    for index in range(model_count):
        require_file(model_dir, template % index, "template_filename_axmodel")
    return config


def disk_usage(path):
    usage = shutil.disk_usage(path)
    return {"total": usage.total, "used": usage.used, "free": usage.free}


def cmm_remaining_kb():
    path = Path("/proc/ax_proc/mem_cmm_info")
    if not path.is_file():
        return None
    match = re.search(r"remain=(\d+)KB", path.read_text(encoding="utf-8", errors="replace"))
    return int(match.group(1)) if match else None


def ddr_available_kb():
    path = Path("/proc/meminfo")
    if not path.is_file():
        return None
    match = re.search(r"^MemAvailable:\s+(\d+)\s+kB$", path.read_text(encoding="utf-8"), re.MULTILINE)
    return int(match.group(1)) if match else None


def resource_snapshot(model_root):
    return {
        "cmm_remaining_kb": cmm_remaining_kb(),
        "ddr_available_kb": ddr_available_kb(),
        "flash": disk_usage(model_root),
    }


def directory_size_bytes(path):
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def dynamic_load_overlay(model_dir, pool_size):
    if pool_size <= 0:
        return model_dir
    overlay_dir = model_dir.parent / f"{model_dir.name}.dynamic-{pool_size}"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    for source in model_dir.iterdir():
        if source.name in {"config.json", ".cache"}:
            continue
        target = overlay_dir / source.name
        if not target.exists():
            target.symlink_to(source)
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    config["dynamic_load_enable"] = True
    config["dynamic_load_pool_size"] = pool_size
    (overlay_dir / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return overlay_dir


def main():
    args = parse_args()
    args.model_root.mkdir(parents=True, exist_ok=True)
    args.result_dir.mkdir(parents=True, exist_ok=True)
    token = os.getenv("HF_TOKEN") or None
    api = HfApi(token=token)
    info = api.model_info(args.model_id, revision=args.revision)
    revision = info.sha
    model_dir = args.model_root / args.model_id.replace("/", "--") / revision
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"下载模型 {args.model_id}，revision={revision}", flush=True)
    snapshot_download(
        repo_id=args.model_id,
        revision=revision,
        local_dir=str(model_dir),
        token=token,
    )
    config = verify_model_files(model_dir)
    test_model_dir = dynamic_load_overlay(model_dir, args.dynamic_load_pool)
    verify_model_files(test_model_dir)
    summary = {
        "model_id": args.model_id,
        "revision": revision,
        "model_dir": str(model_dir),
        "test_model_dir": str(test_model_dir),
        "tokenizer_type": config.get("tokenizer_type"),
        "axmodel_num": config["axmodel_num"],
        "model_size_bytes": directory_size_bytes(model_dir),
        "dynamic_load_pool_size": args.dynamic_load_pool,
        "media": "image" if args.image else "video" if args.video else "audio" if args.audio else "text",
        "disk": disk_usage(args.model_root),
        "status": "downloaded",
    }

    if args.binary is not None:
        if not args.binary.is_file() or not os.access(args.binary, os.X_OK):
            raise RuntimeError(f"冒烟程序不可执行: {args.binary}")
        command = [
            str(args.binary),
            str(test_model_dir),
            str(args.max_tokens),
            "--prompt",
            args.prompt,
        ]
        if args.image is not None:
            command.extend(["--image", str(args.image)])
        elif args.video is not None:
            command.extend(["--video", str(args.video)])
        elif args.audio is not None:
            command.extend(["--audio", str(args.audio)])
        log_path = args.result_dir / "llm_smoke.log"
        summary["resources_before"] = resource_snapshot(args.model_root)
        print("执行: " + " ".join(command), flush=True)
        started_at = time.monotonic()
        try:
            with log_path.open("w", encoding="utf-8") as log_file:
                completed = subprocess.run(
                    command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=args.timeout_seconds,
                    check=False,
                )
            output = log_path.read_text(encoding="utf-8", errors="replace")
            summary["return_code"] = completed.returncode
            decode_rates = re.findall(r"decode avg\s+([0-9.]+)\s+token/s", output)
            if decode_rates:
                summary["decode_tokens_per_second"] = float(decode_rates[-1])
            if completed.returncode != 0:
                raise RuntimeError(f"llm_smoke 退出码异常: {completed.returncode}")
            if "[SMOKE OK]" not in output:
                raise RuntimeError("llm_smoke 未输出成功标记")
            summary["status"] = "passed"
        except Exception as error:
            summary["status"] = "failed"
            summary["error"] = str(error)
            raise
        finally:
            summary["duration_seconds"] = round(time.monotonic() - started_at, 3)
            summary["resources_after"] = resource_snapshot(args.model_root)
            (args.result_dir / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if args.binary is None:
        (args.result_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"验证失败: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
