#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--model", default="all")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--download-timeout-seconds", type=int, default=900)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--cmm-leak-limit-mb", type=int, default=64)
    parser.add_argument("--list", action="store_true")
    return parser.parse_args()


def cmm_remaining_kb():
    path = Path("/proc/ax_proc/mem_cmm_info")
    if not path.is_file():
        return None
    match = re.search(r"remain=(\d+)KB", path.read_text(encoding="utf-8", errors="replace"))
    return int(match.group(1)) if match else None


def load_models(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    models = manifest.get("models")
    if not isinstance(models, list):
        raise RuntimeError("模型清单必须包含 models 数组")
    keys = set()
    for model in models:
        for field in ("key", "model_id", "revision", "input"):
            if not model.get(field):
                raise RuntimeError(f"模型清单缺少字段 {field}: {model}")
        if model["key"] in keys:
            raise RuntimeError(f"模型 key 重复: {model['key']}")
        if model["input"] not in {"text", "image", "video", "audio"}:
            raise RuntimeError(f"不支持的输入类型: {model['input']}")
        if model["input"] != "text" and not model.get("fixture"):
            raise RuntimeError(f"多模态模型缺少 fixture: {model['key']}")
        keys.add(model["key"])
    return models


def fixture_path(repo_root, model):
    fixture = model.get("fixture")
    if not fixture:
        return None
    path = Path(fixture)
    if not path.is_absolute():
        path = repo_root / path
    if not path.is_file() and model["input"] != "video":
        raise RuntimeError(f"测试夹具不存在: {path}")
    return path


def load_model_summary(result_dir):
    path = result_dir / "summary.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    args = parse_args()
    models = load_models(args.manifest)
    if args.list:
        for model in models:
            print(model["key"])
        return

    if args.model_root is None or args.result_root is None:
        raise RuntimeError("执行验证时必须提供 --model-root 和 --result-root")
    selected = [
        model for model in models
        if model.get("enabled", True) and (args.model == "all" or model["key"] == args.model)
    ]
    if not selected:
        raise RuntimeError(f"未找到可执行模型: {args.model}")
    if args.binary is None:
        raise RuntimeError("缺少 --binary")

    repo_root = Path(__file__).resolve().parents[2]
    model_script = Path(__file__).with_name("model_smoke.py")
    args.result_root.mkdir(parents=True, exist_ok=True)
    results = []
    stop_after_leak = False
    for model in selected:
        before_cmm = cmm_remaining_kb()
        result_dir = args.result_root / model["key"]
        command = [
            sys.executable,
            str(model_script),
            "--model-id", model["model_id"],
            "--revision", model["revision"],
            "--model-root", str(args.model_root),
            "--result-dir", str(result_dir),
            "--binary", str(args.binary),
            "--max-tokens", str(model.get("max_tokens", 8)),
            "--download-timeout-seconds", str(
                model.get("download_timeout_seconds", args.download_timeout_seconds)
            ),
            "--timeout-seconds", str(args.timeout_seconds),
            "--prompt", model.get("prompt", "请用一个词回答：测试。"),
            "--dynamic-load-pool", str(model.get("dynamic_load_pool", 0)),
        ]
        fixture = fixture_path(repo_root, model)
        if fixture is not None:
            command.extend([f"--{model['input']}", str(fixture)])
        print(f"开始验证模型: {model['key']}", flush=True)
        completed = subprocess.run(command, check=False)
        after_cmm = cmm_remaining_kb()
        model_summary = load_model_summary(result_dir)
        result = {
            "key": model["key"],
            "model_id": model["model_id"],
            "revision": model["revision"],
            "input": model["input"],
            "return_code": completed.returncode,
            "cmm_before_kb": before_cmm,
            "cmm_after_kb": after_cmm,
            "status": "passed" if completed.returncode == 0 else "failed",
        }
        for field in (
            "decode_tokens_per_second",
            "duration_seconds",
            "model_size_bytes",
            "resources_before",
            "resources_after",
        ):
            if field in model_summary:
                result[field] = model_summary[field]
        if before_cmm is not None and after_cmm is not None:
            leak_kb = before_cmm - after_cmm
            result["cmm_leak_kb"] = leak_kb
            if leak_kb > args.cmm_leak_limit_mb * 1024:
                result["status"] = "failed"
                result["error"] = "CMM 未恢复到允许范围，停止后续模型验证"
                stop_after_leak = True
        results.append(result)
        if stop_after_leak:
            break

    summary = {
        "status": "passed" if all(item["status"] == "passed" for item in results) else "failed",
        "models": results,
    }
    (args.result_root / "matrix-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if summary["status"] != "passed":
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"模型清单验证失败: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
