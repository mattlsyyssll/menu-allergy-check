#!/usr/bin/env python3
"""Split the batch runner's JSON download into the kit's per-case files.

Usage: python3 -I scripts/split_run.py run.json OUT_DIR
Writes OUT_DIR/<CASE>.reply.txt and OUT_DIR/<CASE>.cloudlog.jsonl for every case,
then save each one with:
  python3 -I scripts/testkit/runs.py save kit.json CASE app-<build-id> OUT_DIR/CASE.reply.txt --transcript OUT_DIR/CASE.cloudlog.jsonl
"""
import json
import os
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__)
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
os.makedirs(sys.argv[2], exist_ok=True)
for case, r in data["cases"].items():
    with open(os.path.join(sys.argv[2], f"{case}.reply.txt"), "w", encoding="utf-8") as f:
        f.write(r["reply_txt"])
    with open(os.path.join(sys.argv[2], f"{case}.cloudlog.jsonl"), "w", encoding="utf-8") as f:
        f.write(r["cloudlog_jsonl"])
    note = "" if r.get("status") == "ok" else f"  (status: {r.get('status')} {r.get('error', '')})"
    print(f"{case}: wrote reply and cloud log{note}")
