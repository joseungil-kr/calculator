#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--revision", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
digest = hashlib.sha256()
files = sorted(p for p in (args.root / "dist").rglob("*") if p.is_file())
if not files: raise SystemExit("Cannot attest an empty build")
for file in files:
    digest.update(str(file.relative_to(args.root / "dist")).encode() + b"\0")
    digest.update(file.read_bytes())
result = {"revision": args.revision, "buildSha256": digest.hexdigest(), "buildFiles": len(files), "manifestSha256": hashlib.sha256((args.root / "src/data/publish-manifest.json").read_bytes()).hexdigest(), "node": subprocess.check_output(["node", "--version"], text=True).strip(), "gates": ["build", "static", "graph"], "state": "local_gates_passed", "independentApproval": False}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
