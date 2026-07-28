#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--updates", required=True, type=Path)
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    args = parse_args()
    manifest = load_json(args.manifest)
    models = manifest.get("models")
    if not isinstance(models, list):
        raise RuntimeError("模型清单必须包含 models 数组")

    updates = load_json(args.updates).get("updates")
    if not isinstance(updates, list) or not updates:
        raise RuntimeError("更新记录必须包含非空 updates 数组")

    models_by_key = {}
    for model in models:
        key = model.get("key")
        if not key or key in models_by_key:
            raise RuntimeError(f"模型清单 key 无效或重复: {key}")
        models_by_key[key] = model

    update_keys = set()
    for update in updates:
        key = update.get("key")
        previous_revision = update.get("previous_revision")
        revision = update.get("revision")
        if not key or not previous_revision or not revision:
            raise RuntimeError(f"更新记录缺少必填字段: {update}")
        if key in update_keys:
            raise RuntimeError(f"更新记录 key 重复: {key}")
        if key not in models_by_key:
            raise RuntimeError(f"模型清单中不存在更新记录: {key}")
        model = models_by_key[key]
        if model.get("revision") != previous_revision:
            raise RuntimeError(
                f"模型 {key} 的 revision 已变化，拒绝覆盖: "
                f"期望 {previous_revision}，实际 {model.get('revision')}"
            )
        model["revision"] = revision
        update_keys.add(key)
        print(f"更新模型 revision: {key} {previous_revision} -> {revision}", flush=True)

    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"更新模型 revision 失败: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
