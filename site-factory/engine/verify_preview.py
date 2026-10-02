#!/usr/bin/env python3
"""Truthful public noindex preview verification with bounded safe diagnostics."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

SAFE_FAILURE_PATHS = {
    "home": "/",
    "robots": "/robots.txt",
    "detail": "/funeral/ilsan-paik-funeral-wreath/",
    "funeral_hub": "/funeral/",
}


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "meta":
            values = dict(attrs)
            if values.get("name"):
                self.meta[values["name"].lower()] = values.get("content", "")


def describe_failure(error):
    if isinstance(error, HTTPError):
        # No raw header or body values are logged. Some 403 pages reflect
        # Authorization/Cookie data, so even a short excerpt is unsafe.
        ray = error.headers.get("CF-RAY", "")
        content_type = error.headers.get("Content-Type", "").lower().split(";", 1)[0]
        try:
            body = error.read(65)
        except Exception:
            body = b""
        match = re.fullmatch(br"error code: ([0-9]+)(?:\r?\n)?", body) if len(body) <= 64 else None
        step = getattr(error, "site_factory_step", "unknown")
        step = step if step in SAFE_FAILURE_PATHS else "unknown"
        return {
            "kind": "http",
            "status": int(error.code),
            "atUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "step": step,
            "url": safe_request_url(getattr(error, "site_factory_origin", ""), step),
            "serverIsCloudflare": error.headers.get("Server", "").lower() == "cloudflare",
            "cfRay": ray if re.fullmatch(r"[0-9a-fA-F]{16}-[A-Z]{3}", ray) else None,
            "viaPresent": bool(error.headers.get("Via")),
            "contentType": content_type if content_type in {"text/html", "text/plain", "application/json"} else "other",
            "errorCode": match.group(1).decode("ascii") if match else "withheld",
        }
    return {"kind": type(error).__name__}


def robots_blocks_all(robots):
    # Contract for our generated isolated preview, not a general robots
    # interpreter. Any extra group or Allow rule requires fresh review.
    directives = []
    for raw in robots.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            return False
        name, value = (part.strip().lower() for part in line.split(":", 1))
        directives.append((name, value))
    return directives == [("user-agent", "*"), ("disallow", "/")]


def safe_request_url(origin, step):
    if step not in SAFE_FAILURE_PATHS:
        return None
    try:
        parts = urlsplit(origin)
    except ValueError:
        return None
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
    ):
        return None
    try:
        host = parts.hostname
        if ":" in host:
            host = f"[{host}]"
        if parts.port is not None:
            host = f"{host}:{parts.port}"
    except ValueError:
        return None
    return urlunsplit((parts.scheme, host, SAFE_FAILURE_PATHS[step], "", ""))


def safe_origin(origin):
    url = safe_request_url(origin, "home")
    return url[:-1] if url else None


def verify_once(origin, revision, opener=urlopen):
    base = origin.rstrip("/")
    req = Request(base + "/", headers={"User-Agent": "SiteFactory-StagingQA/3.0"})
    try:
        with opener(req, timeout=15) as response:
            page = response.read().decode("utf-8")
            robot_header = response.headers.get("X-Robots-Tag", "")
    except HTTPError as error:
        error.site_factory_step = "home"
        error.site_factory_origin = origin
        raise
    parsed = MetaParser()
    parsed.feed(page)
    robots_meta = {part.strip().lower() for part in parsed.meta.get("robots", "").split(",")}
    if "noindex" not in robots_meta or parsed.meta.get("site-factory-revision") != revision:
        raise ValueError("revision_or_noindex_mismatch")
    header_directives = {part.strip().lower() for part in robot_header.split(",")}
    if "noindex" not in header_directives:
        raise ValueError("x_robots_header_mismatch")
    robots_url = base + "/robots.txt"
    try:
        with opener(robots_url, timeout=15) as response:
            robots = response.read().decode("utf-8")
    except HTTPError as error:
        error.site_factory_step = "robots"
        error.site_factory_origin = origin
        raise
    if not robots_blocks_all(robots):
        raise ValueError("robots_disallow_mismatch")


def verify(origin, revision, attempts=12, delay=5, opener=urlopen, sleeper=time.sleep):
    failures = []
    for attempt in range(1, attempts + 1):
        try:
            verify_once(origin, revision, opener)
            return {"state": "preview_verified", "origin": safe_origin(origin), "revision": revision, "attempts": attempt}
        except Exception as error:
            detail = describe_failure(error)
            failures.append(detail)
            print(f"Preview verification {attempt}/{attempts}: {json.dumps(detail, ensure_ascii=False)}", flush=True)
            if attempt < attempts:
                sleeper(delay)
    return {"state": "preview_verification_failed", "origin": safe_origin(origin), "revision": revision, "attempts": attempts, "lastFailure": failures[-1]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("A pinned 40-character revision is required")
    result = verify(args.origin, args.revision)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if result["state"] != "preview_verified":
        raise SystemExit("PREVIEW_VERIFICATION_FAILED: see sanitized report")
    print("PREVIEW_VERIFIED " + (result["origin"] or "withheld"))


if __name__ == "__main__":
    main()
