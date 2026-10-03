#!/usr/bin/env python3
"""Verify the deployed revision, complete route set and immutable snapshots.

A deploy command passing is not live_verified. 403 and transient network errors
remain explicit incomplete results and always return a nonzero exit code.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.metas, self.canonicals, self.snapshots = {}, [], []
        self.h1 = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta": self.metas[a.get("name")] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical": self.canonicals.append(a.get("href"))
        if tag == "h1": self.h1 += 1
        if a.get("data-snapshot-id"): self.snapshots.append(a["data-snapshot-id"])


def validate_html(html, origin, route, revision, snapshot=None, indexable=True, robot_header=""):
    doc = Document(html)
    assert doc.metas.get("site-factory-revision") == revision, f"Revision mismatch at {route}"
    robots = doc.metas.get("robots", "").lower()
    if indexable:
        assert "index,follow" in robots and "noindex" not in robots, f"Unindexable {route}"
        assert "noindex" not in robot_header.lower(), f"Stale X-Robots-Tag noindex at {route}"
    else:
        assert "noindex" in robots, f"Missing noindex at {route}"
        assert "noindex" in robot_header.lower(), f"Missing X-Robots-Tag noindex at {route}"
    assert doc.h1 == 1, f"Expected one H1 at {route}"
    assert [unquote(url or "") for url in doc.canonicals] == [origin + route], f"Canonical mismatch at {route}"
    if snapshot: assert snapshot in doc.snapshots, f"Snapshot mismatch at {route}"
    assert "application/ld+json" in html, f"Missing schema at {route}"
    return doc


def verify(root, origin, revision, fetch, naver_verification="", indexnow_key=""):
    manifest = json.loads((root / "src/data/publish-manifest.json").read_text())
    architecture = json.loads((root / "src/data/architecture.json").read_text()) if (root / "src/data/architecture.json").exists() else {}
    routes = {"/": (None, True)}
    routes.update({p["url"]: (p["snapshotId"], True) for p in manifest["pages"] if p.get("status") == "approved"})
    routes.update({h["url"]: (None, h.get("children", 0) >= 3) for h in architecture.get("hubs", []) if h.get("children", 0) > 0})
    def response(route):
        value = fetch(route)
        status, html = value[:2]
        headers = value[2] if len(value) > 2 else {}
        return status, html, {str(k).lower(): str(v) for k, v in headers.items()}
    fingerprint = hashlib.sha256()
    for route, (snapshot, indexable) in sorted(routes.items()):
        status, html, headers = response(route)
        if status == 403: raise PermissionError(f"Live QA blocked by HTTP403 at {route}; independent browser verification is required")
        assert status == 200, f"HTTP{status} at {route}"
        doc = validate_html(html, origin, route, revision, snapshot, indexable, headers.get("x-robots-tag", ""))
        if route == "/" and naver_verification:
            assert doc.metas.get("naver-site-verification") == naver_verification
        fingerprint.update(html.encode())
    status, robots, _ = response("/robots.txt")
    assert status == 200 and "Allow: /" in robots and "Disallow: /" not in robots
    assert f"Sitemap: {origin}/sitemap-index.xml" in robots
    if indexnow_key:
        status, body, _ = response(f"/{indexnow_key}.txt")
        assert status == 200 and body.strip() == indexnow_key, "IndexNow ownership file mismatch"
    status, index, index_headers = response("/sitemap-index.xml")
    assert status == 200
    assert "noindex" not in index_headers.get("x-robots-tag", "").lower(), "Sitemap has stale noindex header"
    files = re.findall(r"<loc>(.*?)</loc>", index)
    assert files and all(url.startswith(origin + "/") for url in files)
    sitemap = ""
    for url in files:
        status, content, headers = response(url[len(origin):])
        assert status == 200
        assert "noindex" not in headers.get("x-robots-tag", "").lower(), "Sitemap child has stale noindex header"
        sitemap += unquote(content)
    expected_sitemap = {origin + route for route, (_, indexable) in routes.items() if indexable}
    actual_sitemap = set(re.findall(r"<loc>(.*?)</loc>", sitemap))
    assert actual_sitemap == expected_sitemap, f"Unexpected sitemap set: {actual_sitemap ^ expected_sitemap}"
    for route, (_, indexable) in routes.items():
        if not indexable: continue
        assert f"<loc>{origin}{route}</loc>" in sitemap, f"Missing sitemap route {route}"
    status, body, headers = response("/site-factory-live-qa-definitely-not-found/")
    assert status == 404 and "페이지를 찾을 수 없습니다" in body
    assert "noindex" in headers.get("x-robots-tag", "").lower(), "404 missing X-Robots-Tag noindex"
    return {"pipelineState": "live_verified", "revision": revision, "origin": origin, "routes": len(routes), "manifestPages": len(manifest["pages"]), "htmlSha256": fingerprint.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--delay", type=float, default=5)
    parser.add_argument("--report", default="live-qa-report.json")
    parser.add_argument("--naver-verification", default="")
    parser.add_argument("--indexnow-key", default="")
    args = parser.parse_args()
    assert re.fullmatch(r"[0-9a-f]{40}", args.revision), "Expected full pinned commit SHA"
    origin = args.origin.rstrip("/")
    def fetch(route):
        request = Request(origin + quote(route, safe="/%?=&"), headers={"User-Agent": "SiteFactory-LiveQA/3.0", "Cache-Control": "no-cache"})
        try:
            with urlopen(request, timeout=15) as response:
                return response.status, response.read().decode("utf-8", "replace"), dict(response.headers.items())
        except HTTPError as error:
            return error.code, error.read().decode("utf-8", "replace"), dict(error.headers.items())
    result = None
    for attempt in range(args.attempts):
        try:
            result = verify(args.root, origin, args.revision, fetch, args.naver_verification, args.indexnow_key)
            break
        except PermissionError as error:
            result = {"pipelineState": "verification_blocked", "revision": args.revision, "reason": str(error)}
            break
        except (AssertionError, URLError, TimeoutError, OSError) as error:
            result = {"pipelineState": "verification_failed", "revision": args.revision, "reason": str(error)}
            print(f"Live verification attempt {attempt + 1}/{args.attempts}: {error}")
            if attempt + 1 < args.attempts: time.sleep(args.delay)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if result["pipelineState"] != "live_verified": raise SystemExit(2)


if __name__ == "__main__": main()
