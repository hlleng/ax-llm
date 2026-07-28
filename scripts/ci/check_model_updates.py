#!/usr/bin/env python3
import argparse
import copy
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    return parser.parse_args()


def load_models(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    models = manifest.get("models")
    if not isinstance(models, list):
        raise RuntimeError("模型清单必须包含 models 数组")
    return models


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    args = parse_args()
    api = HfApi(token=os.getenv("HF_TOKEN") or None)
    updates = []
    candidates = []

    for model in load_models(args.manifest):
        if not model.get("enabled", True):
            print(f"跳过未启用模型: {model.get('key', '<unknown>')}", flush=True)
            continue
        for field in ("key", "model_id", "revision"):
            if not model.get(field):
                raise RuntimeError(f"模型清单缺少字段 {field}: {model}")

        try:
            latest_revision = api.model_info(model["model_id"]).sha
        except Exception as error:
            raise RuntimeError(f"查询模型更新失败: {model['model_id']}: {error}") from error
        if not latest_revision:
            raise RuntimeError(f"模型未返回 revision: {model['model_id']}")
        if latest_revision == model["revision"]:
            print(f"模型无更新: {model['key']} ({latest_revision})", flush=True)
            continue

        candidate = copy.deepcopy(model)
        candidate["revision"] = latest_revision
        candidates.append(candidate)
        updates.append(
            {
                "key": model["key"],
                "model_id": model["model_id"],
                "previous_revision": model["revision"],
                "revision": latest_revision,
            }
        )
        print(
            f"发现模型更新: {model['key']} "
            f"{model['revision']} -> {latest_revision}",
            flush=True,
        )

    write_json(args.candidate_manifest, {"models": candidates})
    write_json(
        args.summary,
        {
            "has_updates": bool(updates),
            "updates": updates,
        },
    )
    print(f"检测完成，待验证模型数: {len(updates)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"模型更新检测失败: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
