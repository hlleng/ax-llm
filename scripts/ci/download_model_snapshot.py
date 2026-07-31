#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from huggingface_hub import snapshot_download


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--model-dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    args.model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=args.model_id,
        revision=args.revision,
        local_dir=str(args.model_dir),
        token=os.getenv("HF_TOKEN") or None,
    )


if __name__ == "__main__":
    main()
