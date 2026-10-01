#!/usr/bin/env python3
"""Calculate review integrity metadata without writing files or approving copy."""
import argparse
import json
from pathlib import Path
import sys
from render_snapshot import SnapshotError, parse_payload, validate_content, frozen_hashes

parser = argparse.ArgumentParser()
parser.add_argument("--payload", type=Path)
args = parser.parse_args()
body = args.payload.read_text(encoding="utf-8") if args.payload else sys.stdin.read()
try:
    p = validate_content(parse_payload(body))
    storage, reviewed = frozen_hashes(p)
except SnapshotError as error:
    raise SystemExit(f"PROOF INPUT INVALID: {error}")
print(json.dumps({"algorithm": "site-factory-review-sha256-v1", "siteKey": p["SITE_KEY"], "pageKey": p["PAGE_KEY"], "snapshotId": p["SNAPSHOT_ID"], "approvedSnapshotHash": reviewed, "snapshotHash": storage, "approvalGranted": False}, ensure_ascii=False))
