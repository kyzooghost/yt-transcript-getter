#!/usr/bin/env python3
"""Merge per-account JSONL files into one posts-<run>.jsonl in handle order.

Validates each line parses as JSON; skips and counts invalid lines.
Missing per-account files are listed as skipped (not fatal).

Usage:
    merge.py --run <YYYYMMDD-HHMM> --out-dir output --handles h1 h2 ...
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out-dir", default="output")
    ap.add_argument("--handles", nargs="+", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_path = out_dir / f"posts-{args.run}.jsonl"

    total = 0
    invalid = 0
    missing: list[str] = []
    with merged_path.open("w", encoding="utf-8") as out:
        for h in args.handles:
            p = out_dir / f"{h}-{args.run}.jsonl"
            if not p.exists():
                missing.append(h)
                print(f"[merge] SKIP missing {p}", file=sys.stderr)
                continue
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        invalid += 1
                        continue
                    out.write(line + "\n")
                    total += 1

    print(f"merged={merged_path} lines={total} invalid={invalid} missing={missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
