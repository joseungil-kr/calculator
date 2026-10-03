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
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET


GOYANG_SITE = "goyang-flower-v2"
GOYANG_SCOPE = "goyang-flower-v2-dong-coverage-20261003"
GOYANG_ORIGIN = "https://goyang.fwith.kr"
GOYANG_BASELINE = "e4eead3e881b3b4c09a60e2af5befb55b6787413"
GOYANG_BASELINE_TREE = "27a45b8e99151c34b966f0a59a96110b91395fad"
GOYANG_CANARY = "goyang-ilsan-paik-r2-20261002T040830"
GOYANG_CANARY_HASH = "1419cc48f44a3618cbc365ac7f3796d4cd35dc5522eeff655a22f4caadfbdf10"
# Observed on the existing bound Goyang host. This digest pins every byte of
# Cloudflare's single public analytics element, including all attributes/values.
GOYANG_CF_BEACON_SRC = b"https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495"
GOYANG_CF_BEACON_SHA256 = "8a5cd48fb3f913d009a128498bef6fadc43d5561daec87e79f6adcd0bcc903f5"


def goyang_artifact_matches(html, artifact, allow_managed_beacon=False):
    live = html.encode("utf-8")
    if live == artifact:
        return True
    closing = b"</body></html>"
    if not allow_managed_beacon or not artifact.endswith(closing) or not live.endswith(closing):
        return False
    prefix = artifact[:-len(closing)]
    if not live.startswith(prefix):
        return False
    inserted = live[len(prefix):-len(closing)]
    return (inserted.startswith(b'<script type="module" src="' + GOYANG_CF_BEACON_SRC + b'" ')
            and inserted.endswith(b'</script>\n') and inserted.count(b'<script') == 1
            and hashlib.sha256(inserted).hexdigest() == GOYANG_CF_BEACON_SHA256)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def resolve_goyang_coverage_target(site, repository, revision, launch_key, scope_key, phase, version_preview=False):
    """Trusted-main opt-in; a caller's scope string alone never authorizes release."""
    require(phase in {"preview", "production"}, "Unsupported Goyang phase")
    require(launch_key == scope_key == GOYANG_SCOPE, "Goyang coverage scope mismatch")
    identity = {"repo": "joseungil-kr/fwith-site-factory", "branch": "site-factory-goyang-v2",
                "root": "site-factory/goyang-flower", "siteUrl": GOYANG_ORIGIN,
                "templateKey": "flower-local-v2", "snapshotRenderer": "structured-json-v12",
                "worker": "goyang-flower-prod-disabled", "stagingUrl": "https://goyang-flower-guide-qa.joseungil.workers.dev",
                "stagingWranglerConfig": "wrangler.staging.jsonc"}
    require(repository == identity["repo"] and all(site.get(k) == v for k, v in identity.items()),
            "Goyang registered identity mismatch")
    require(site.get("growthPaused") is True and site.get("autoDeploySnapshots") is False
            and site.get("requireRevisionApproval") is True and site.get("requireSnapshotApproval") is True,
            "Goyang paused approval policy mismatch")
    require(site.get("indexnowKey") == "" and site.get("naverVerification") == "",
            "Goyang coverage must preserve its current ownership configuration")
    require(site.get("administrativeCoverage") == {"enabled": True, "regionKey": "goyang", "unitBasis": "legal"}
            and site.get("categoryPageTypes", {}).get("regions") == ["regional-service"], "Goyang region opt-in missing")
    config = site.get("coverageDeployment", {})
    require(config.get("enabled") is True, "Goyang coverage deployment opt-in is closed")
    require(config.get("launchKey") == config.get("scopeKey") == GOYANG_SCOPE,
            "Trusted Goyang scope binding mismatch")
    require(config.get("canonicalOrigin") == GOYANG_ORIGIN and config.get("worker") == "goyang-flower-guide-qa"
            and config.get("wranglerConfig") == "wrangler.staging.jsonc", "Goyang bound deployment target mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", revision or "") is not None, "Pinned Goyang revision required")
    approved = config.get("previewRevision") if phase == "preview" else site.get("approvedRevision")
    evidence = config.get("previewApprovalEvidenceUrl") if phase == "preview" else site.get("approvalEvidenceUrl")
    require(approved == revision and re.fullmatch(
        r"https://github\.com/joseungil-kr/fwith-site-factory/(?:issues|pull|commit)/[^\s?#]+(?:#[^\s]+)?",
        evidence or "") is not None, "Exact Goyang revision lacks trusted review evidence")
    digest = config.get(phase + "ManifestSha256", "")
    require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "Reviewed Goyang manifest digest required")
    if phase == "preview":
        paused = site.get("productionEnabled") is False and site.get("launchMode") == "staging"
        live = site.get("productionEnabled") is True and site.get("launchMode") == "live"
        require(paused or (version_preview and live), "Goyang live preview requires non-deploying version isolation")
    else:
        require(site.get("productionEnabled") is True and site.get("launchMode") == "live",
                "Production Launch Gate is closed")
    return {"site_key": GOYANG_SITE, "branch": identity["branch"], "root": identity["root"],
            "url": GOYANG_ORIGIN, "site_url": GOYANG_ORIGIN, "worker": config["worker"],
            "staging_worker": config["worker"], "config": config["wranglerConfig"],
            "wrangler": config["wranglerConfig"], "revision": revision, "isolated": "true",
            "goyang_coverage": "true", "launch_key": launch_key, "scope_key": scope_key,
            "manifest_sha256": digest, "build_root": "preview-build" if phase == "preview" else "release-build",
            "graph": site.get("graphScript", "scripts/qa_graph.mjs"),
            "naver": site.get("naverVerification", ""), "indexnow": site.get("indexnowKey", "")}


def validate_goyang_coverage_source(root, baseline_root, manifest_digest, phase, version_preview=False):
    """Validate the reviewed source and preserve the complete historical canary record."""
    root, baseline_root = Path(root), Path(baseline_root)
    read = lambda base, name: json.loads((base / "src/data" / name).read_text())
    manifest_bytes = (root / "src/data/publish-manifest.json").read_bytes()
    require(hashlib.sha256(manifest_bytes).hexdigest() == manifest_digest, "Goyang manifest digest mismatch")
    manifest, baseline_manifest = json.loads(manifest_bytes), read(baseline_root, "publish-manifest.json")
    require(manifest.get("siteKey") == GOYANG_SITE and manifest.get("snapshotMode") == "git-frozen",
            "Goyang frozen manifest identity mismatch")
    baseline_pages = read(baseline_root, "pages.json")
    require(len(baseline_manifest["pages"]) == len(baseline_pages) == 1
            and baseline_pages[0].get("snapshotId") == GOYANG_CANARY
            and baseline_pages[0].get("snapshotHash") == GOYANG_CANARY_HASH, "Invalid fixed canary baseline")
    pages, architecture, mapping = read(root, "pages.json"), read(root, "architecture.json"), read(root, "page-map.json")
    require(mapping.get("pages") == manifest["pages"], "Page map differs from frozen manifest")
    def indexed(rows, key):
        values = [row.get(key) for row in rows]
        require(all(values) and len(set(values)) == len(values), "Duplicate or missing frozen identity")
        return dict(zip(values, rows))
    by_key, manifests, nodes = indexed(pages, "pageKey"), indexed(manifest["pages"], "pageKey"), indexed(architecture["pages"], "pageKey")
    require(by_key.keys() == manifests.keys() == nodes.keys(), "Source/manifest/architecture set mismatch")
    indexed(pages, "url"); indexed(pages, "snapshotId")
    old = baseline_pages[0]; old_key = old["pageKey"]
    require(by_key.get(old_key) == old and manifests.get(old_key) == baseline_manifest["pages"][0], "Frozen canary was changed")
    require(manifest.get("snapshotLedger", {}).get(GOYANG_CANARY) == baseline_manifest["snapshotLedger"][GOYANG_CANARY],
            "Frozen canary ledger was changed")
    for name in ("products.json", "business-truth.json"):
        require((root / "src/data" / name).read_bytes() == (baseline_root / "src/data" / name).read_bytes(),
                "Historical product or business source was changed")
    for original in (baseline_root / "public/images").rglob("*"):
        if original.is_file():
            candidate = root / original.relative_to(baseline_root)
            require(candidate.is_file() and candidate.read_bytes() == original.read_bytes(), "Historical product image was changed")
    config = read(root, "site-config.json")
    approved = config.get("productionApproved")
    require(config.get("siteKey") == GOYANG_SITE and type(approved) is bool
            and (approved is (phase == "production") or (phase == "preview" and version_preview)),
            "Goyang source indexing approval mismatch")
    primary = json.loads((root / "wrangler.jsonc").read_text())
    deploy = json.loads((root / "wrangler.staging.jsonc").read_text())
    require(primary == json.loads((baseline_root / "wrangler.jsonc").read_text())
            and deploy == json.loads((baseline_root / "wrangler.staging.jsonc").read_text()),
            "Goyang Wrangler settings differ from the fixed authorized baseline")
    require(primary.get("name") == "goyang-flower-prod-disabled" and deploy.get("name") == "goyang-flower-guide-qa"
            and deploy.get("workers_dev") is True and deploy.get("assets", {}).get("directory") == "./dist/"
            and not any(k in deploy for k in ("route", "routes", "triggers")), "Goyang config may alter the existing binding")
    if phase == "production":
        require((root / "production-indexing.enabled").is_file(), "Goyang indexing marker missing")
    coverage = read(root, "region-coverage.json")
    require(coverage.get("siteKey") == GOYANG_SITE and coverage.get("scopeKey") == GOYANG_SCOPE
            and coverage.get("unitBasis") == "legal", "Goyang source coverage scope mismatch")
    units = indexed(coverage["units"], "pageKey")
    regional = [p for p in pages if p["pageKey"] != old_key]
    require(regional, "No approved regional content in this coverage release")
    for page in pages:
        entry = manifests[page["pageKey"]]
        require(page.get("status") == entry.get("status") == "approved" and page.get("approvalVerified") is True
                and entry.get("approvalVerified") is True and all(page.get(k) == v for k, v in entry.items()),
                "Frozen snapshot approval/source mismatch")
        require(re.fullmatch(r"[0-9a-f]{64}", page.get("snapshotHash", "")) is not None,
                "Frozen snapshot hash missing")
        require(all(s.get("url") and s.get("name") and s.get("type") and s.get("verifiedAt") for s in page.get("sources", []))
                and page.get("sources"), "Frozen source provenance missing")
        if page["pageKey"] == old_key:
            continue
        unit, node = units.get(page["pageKey"], {}), nodes[page["pageKey"]]
        require(page.get("category") == "regions" and page.get("pageType") == "regional-service"
                and page.get("routeType") == "category" and page.get("url") == unit.get("url")
                and page.get("slug") == unit.get("slug") and node.get("pageRole") == "REGION_SERVICE_LANDING"
                and node.get("parentHub") == "/regions/" and node.get("localizationPolicy") == "local-required",
                "Unrelated or invalid page in Goyang coverage release")
        require(re.fullmatch(r"[a-z0-9-]+", page["slug"]) and page["url"] == "/regions/" + page["slug"] + "/",
                "Unsafe regional source URL")
    return manifest, architecture


def verify_goyang_coverage(root, baseline_root, origin, revision, manifest_digest, phase, fetch=None, version_preview=False):
    require(origin == GOYANG_ORIGIN, "Goyang canonical origin mismatch")
    manifest, architecture = validate_goyang_coverage_source(root, baseline_root, manifest_digest, phase, version_preview)
    routes = {"/": (None, True)}
    routes.update({p["url"]: (p["snapshotId"], True) for p in manifest["pages"]})
    for hub in architecture["hubs"]:
        require(re.fullmatch(r"[a-z]+", hub["category"]) and hub["url"] == "/" + hub["category"] + "/",
                "Unsafe hub URL")
        children = sum(p["category"] == hub["category"] for p in manifest["pages"])
        require(hub.get("children") == children, "Hub child count differs from actual manifest")
        if children:
            routes[hub["url"]] = (None, children >= 3)
    root = Path(root)
    if phase == "production":
        require(not any((root / "dist/_site-factory/version-probe").rglob("*")), "Preview probe cannot enter production artifact")
    actual_html = {"/" if p.relative_to(root / "dist").as_posix() == "index.html" else "/" + p.parent.relative_to(root / "dist").as_posix() + "/"
                   for p in (root / "dist").rglob("index.html")}
    require(actual_html == set(routes), "Built HTML route set differs from approved manifest/hubs")
    require((root / "dist/404.html").is_file(), "Built 404 missing")
    allowed_html = {root / "dist" / route.lstrip("/") / "index.html" for route in routes} | {root / "dist/404.html"}
    all_html = {p for p in (root / "dist").rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm", ".xhtml"}}
    require(all_html == allowed_html, "Unapproved standalone HTML artifact")
    offline = fetch is None
    if offline:
        # Run the SAME HTML/404/robots/sitemap policy before credentials or deploy.
        # This site emits one global robots rule; unfamiliar overrides fail closed.
        local_headers, pattern = {}, None
        for line in (root / "dist/_headers").read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if not line[0].isspace():
                pattern = line.strip()
            elif "x-robots-tag" in line.lower():
                parts = line.strip().split(":", 1)
                require(pattern == "/*" and len(parts) == 2 and parts[0].lower() == "x-robots-tag"
                        and "x-robots-tag" not in local_headers, "Unsupported local robots header override")
                local_headers["x-robots-tag"] = parts[1].strip()
        def local_fetch(route):
            if route in routes:
                file, status = root / "dist" / route.lstrip("/") / "index.html", 200
            elif route.endswith((".txt", ".xml")) and (root / "dist" / route.lstrip("/")).is_file():
                file, status = root / "dist" / route.lstrip("/"), 200
            else:
                file, status = root / "dist/404.html", 404
            return status, file.read_text(), local_headers
        fetch = local_fetch
    def response(route):
        require(route.startswith("/") and not route.startswith("//") and ".." not in route and "?" not in route and "#" not in route,
                "Unsafe verification path")
        status, body, headers = fetch(route)
        if status == 403:
            raise PermissionError("Goyang HTTP403; verification remains blocked")
        return status, body, {str(k).lower(): str(v) for k, v in headers.items()}
    for route, (snapshot, production_indexable) in sorted(routes.items()):
        status, html, headers = response(route)
        require(status == 200, "Goyang page HTTP status mismatch")
        indexable = phase == "production" and production_indexable
        doc = validate_html(html, origin, route, revision, snapshot, indexable)
        directives = {v.strip().lower() for v in doc.metas.get("robots", "").split(",")}
        expected = {"index", "follow"} if indexable else ({"noindex", "follow"} if phase == "production" else {"noindex", "nofollow", "noarchive"})
        require(directives == expected, "Goyang exact robots directives mismatch")
        header = {v.strip().lower() for v in headers.get("x-robots-tag", "").split(",") if v.strip()}
        require(("noindex" not in header and "nofollow" not in header) if phase == "production" else header == {"noindex", "nofollow", "noarchive"},
                "Goyang response header policy mismatch")
        require(doc.snapshots == ([snapshot] if snapshot else []), "Goyang exact snapshot identity mismatch")
        file = root / "dist" / route.lstrip("/") / "index.html"
        require(goyang_artifact_matches(html, file.read_bytes(), not offline), "Live HTML differs from reviewed artifact/source/CTA/assets")
    status, robots, _ = response("/robots.txt")
    expected_robots = [("user-agent", "*"), ("disallow", "/")] if phase == "preview" else [("user-agent", "*"), ("allow", "/"), ("sitemap", origin + "/sitemap-index.xml")]
    directives = [tuple(x.strip() for x in line.split(":", 1)) for line in robots.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    require(status == 200 and [(k.lower(), v) for k, v in directives] == expected_robots, "Goyang robots.txt mismatch")
    def locations(path, root_tag, child_tag):
        status, body, headers = response(path)
        require(status == 200 and len(body) <= 1024 * 1024 and "<!" not in body, "Invalid Goyang sitemap response")
        directives = {x.strip().lower() for x in headers.get("x-robots-tag", "").split(",") if x.strip()}
        require("noindex" not in directives if phase == "production" else "noindex" in directives, "Goyang sitemap header mismatch")
        xml = ET.fromstring(body); ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        require(xml.tag == ns + root_tag, "Goyang sitemap type mismatch")
        urls = [unquote(x.text or "") for x in xml.findall(ns + child_tag + "/" + ns + "loc")]
        require(len(xml) == len(urls) == len(set(urls)) and all(u.startswith(origin + "/") for u in urls), "Duplicate or foreign sitemap URL")
        return urls
    files = locations("/sitemap-index.xml", "sitemapindex", "sitemap")
    require(files and all(re.fullmatch(re.escape(origin) + r"/sitemap-\d+\.xml", u) for u in files), "Unexpected Goyang sitemap child")
    urls = [u for f in files for u in locations(f[len(origin):], "urlset", "url")]
    expected_urls = {origin + route for route, (_, indexable) in routes.items() if indexable}
    require(len(urls) == len(set(urls)) and set(urls) == expected_urls, "Goyang exact sitemap set mismatch")
    absent = {"/site-factory-live-qa-definitely-not-found/"}
    absent.update(h["url"] for h in architecture["hubs"] if h["url"] not in routes)
    coverage = json.loads((root / "src/data/region-coverage.json").read_text())
    for unit in coverage["units"]:
        require(re.fullmatch(r"/regions/[a-z0-9-]+/", unit["url"]), "Unsafe unpublished regional route")
        if unit["url"] not in routes:
            absent.add(unit["url"])
    for route in sorted(absent):
        status, html, headers = response(route)
        doc = Document(html)
        expected_robots = "noindex,follow" if phase == "production" else "noindex,nofollow,noarchive"
        require(status == 404 and doc.metas.get("robots") == expected_robots and doc.h1 == 1
                and doc.metas.get("site-factory-revision") == revision and not doc.canonicals
                and not doc.snapshots and "application/ld+json" not in html
                and goyang_artifact_matches(html, (root / "dist/404.html").read_bytes(), not offline), "Goyang 404 artifact/policy mismatch")
        if phase == "preview":
            require("noindex" in {x.strip().lower() for x in headers.get("x-robots-tag", "").split(",")}, "Goyang 404 header missing noindex")
    return {"pipelineState": "goyang_source_validated" if offline else "preview_verified" if phase == "preview" else "live_verified", "revision": revision,
            "origin": origin, "scopeKey": GOYANG_SCOPE, "routes": len(routes), "manifestSha256": manifest_digest,
            "artifactParity": True, "manifestPages": len(manifest["pages"])}


GOYANG_PUBLIC_BOOTSTRAP = "48f0b31e779c399dd47ee1405ba81f974a302a93"
GOYANG_PUBLIC_BOOTSTRAP_MANIFEST = "d930efc3630966607fdd354d00a3a6bbb03a4a75f270e5d6f49466d77ea5360e"
# Independent HTTP/visual evidence: issues/127#issuecomment-5969021992.
def goyang_public_reference(site):
    if site.get("productionEnabled") is False and site.get("launchMode") == "staging":
        return {"revision": GOYANG_PUBLIC_BOOTSTRAP, "manifest_sha256": GOYANG_PUBLIC_BOOTSTRAP_MANIFEST, "phase": "preview"}
    target = resolve_goyang_coverage_target(site, "joseungil-kr/fwith-site-factory",
        site.get("approvedRevision"), GOYANG_SCOPE, GOYANG_SCOPE, "production")
    return {"revision": target["revision"], "manifest_sha256": target["manifest_sha256"], "phase": "production"}


def read_goyang_version_upload(text):
    """Pinned Wrangler 4.146 official NDJSON. Never synthesize a preview URL."""
    require(len(text) <= 1024 * 1024, "Oversized upload result")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    require(all(isinstance(row, dict) for row in rows), "Invalid upload result")
    require(all(row.get("type") in {"wrangler-session", "version-upload"} for row in rows),
            "Failed or non-upload operation in result")
    uploads = [row for row in rows if row.get("type") == "version-upload"]
    require(len(uploads) == 1, "Exactly one confirmed version upload required")
    row = uploads[0]
    version, url = row.get("version_id"), row.get("preview_url")
    require(row.get("version") == 1 and row.get("worker_name") == "goyang-flower-guide-qa"
            and row.get("worker_name_overridden") is False and not row.get("wrangler_environment")
            and not row.get("preview_alias_url"), "Unexpected upload identity/alias")
    require(isinstance(version, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", version), "Missing actual version ID")
    require(isinstance(url, str) and re.fullmatch(r"https://[0-9a-f]{8}-goyang-flower-guide-qa\.joseungil\.workers\.dev", url)
            and urlsplit(url).hostname.split("-", 1)[0] == version[:8], "Unconfirmed or mismatched exact version URL")
    return {"versionId": version, "previewUrl": url}


def verify_goyang_assets(root, fetch, noindex):
    """Exact bytes for every non-HTML asset, including product photos and CSS."""
    count = 0
    for file in sorted((Path(root) / "dist").rglob("*")):
        if not file.is_file() or file.suffix.lower() in {".html", ".htm", ".xhtml"} or file.name in {"_headers", "_redirects"}:
            continue
        route = "/" + file.relative_to(Path(root) / "dist").as_posix()
        status, body, headers = fetch(route)
        if status == 403: raise PermissionError("Goyang asset HTTP403")
        require(status == 200 and body == file.read_bytes(), "Goyang static asset bytes/status mismatch")
        headers = {k.lower(): v for k, v in headers.items()}
        if noindex:
            require({x.strip().lower() for x in headers.get("x-robots-tag", "").split(",")} == {"noindex", "nofollow", "noarchive"}, "Version asset lacks exact noindex headers")
        mime = {".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".png":"image/png", ".webp":"image/webp", ".svg":"image/svg+xml", ".css":"text/css"}.get(file.suffix.lower())
        if mime: require(headers.get("content-type", "").split(";",1)[0].strip() == mime, "Goyang static asset MIME mismatch")
        count += 1
    require(count > 0, "Empty Goyang asset artifact")
    return count


def validate_goyang_probe_path(path):
    require(re.fullmatch(r"/_site-factory/version-probe/[1-9][0-9]*\.txt", path or ""), "Unsafe isolation probe path")
    return path


def verify_goyang_probe_absent(public_root, path, fetch):
    validate_goyang_probe_path(path)
    status, body, _ = fetch(path)
    if status == 403: raise PermissionError("Goyang probe HTTP403")
    require(status == 404 and goyang_artifact_matches(body.decode("utf-8"), (Path(public_root)/"dist/404.html").read_bytes(), True),
            "Version-only probe was exposed on canonical hostname")


def goyang_http_fetch(origin):
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, message, headers, newurl): return None
    opener = build_opener(NoRedirect())
    def fetch(route):
        require(route.startswith("/") and not route.startswith("//") and ".." not in route and not any(c in route for c in "?#\\"), "Unsafe HTTP verification path")
        request = Request(origin + quote(route, safe="/"), headers={"User-Agent": "SiteFactory-GoyangCoverageQA/1.0", "Cache-Control": "no-cache"})
        try:
            response = opener.open(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            require(response.geturl() == request.full_url, "Goyang unexpected redirect")
            body = response.read(8 * 1024 * 1024 + 1)
            require(len(body) <= 8 * 1024 * 1024, "Goyang response too large")
            return response.status, body, dict(response.headers.items())
    return fetch


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


def validate_html(html, origin, route, revision, snapshot=None, indexable=True, robot_header="", strict_seongnam=False):
    doc = Document(html)
    assert doc.metas.get("site-factory-revision") == revision, f"Revision mismatch at {route}"
    robots = doc.metas.get("robots", "").lower()
    if indexable:
        assert "index,follow" in robots and "noindex" not in robots, f"Unindexable {route}"
        if strict_seongnam:
            assert "noindex" not in robot_header.lower(), f"Stale X-Robots-Tag noindex at {route}"
    else:
        assert "noindex" in robots, f"Missing noindex at {route}"
        if strict_seongnam:
            assert "noindex" in robot_header.lower(), f"Missing X-Robots-Tag noindex at {route}"
    assert doc.h1 == 1, f"Expected one H1 at {route}"
    assert [unquote(url or "") for url in doc.canonicals] == [origin + route], f"Canonical mismatch at {route}"
    if snapshot: assert snapshot in doc.snapshots, f"Snapshot mismatch at {route}"
    assert "application/ld+json" in html, f"Missing schema at {route}"
    return doc


def verify(root, origin, revision, fetch, naver_verification="", indexnow_key="", site_key=""):
    manifest = json.loads((root / "src/data/publish-manifest.json").read_text())
    architecture = json.loads((root / "src/data/architecture.json").read_text()) if (root / "src/data/architecture.json").exists() else {}
    # Keep other registered sites on their established verification contract.
    # Only the explicitly selected Seongnam release includes thin-hub/header/404 checks.
    strict_seongnam = site_key == "seongnam-flower-v2"
    routes = {"/": (None, True)}
    routes.update({p["url"]: (p["snapshotId"], True) for p in manifest["pages"] if p.get("status") == "approved"})
    if strict_seongnam:
        routes.update({h["url"]: (None, h.get("children", 0) >= 3) for h in architecture.get("hubs", []) if h.get("children", 0) > 0})
    else:
        routes.update({h["url"]: (None, True) for h in architecture.get("hubs", []) if h.get("children", 1) > 0 and h.get("indexable", True)})
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
        doc = validate_html(html, origin, route, revision, snapshot, indexable, headers.get("x-robots-tag", ""), strict_seongnam)
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
    if strict_seongnam:
        assert "noindex" not in index_headers.get("x-robots-tag", "").lower(), "Sitemap has stale noindex header"
    files = re.findall(r"<loc>(.*?)</loc>", index)
    assert files and all(url.startswith(origin + "/") for url in files)
    sitemap = ""
    for url in files:
        status, content, headers = response(url[len(origin):])
        assert status == 200
        if strict_seongnam:
            assert "noindex" not in headers.get("x-robots-tag", "").lower(), "Sitemap child has stale noindex header"
        sitemap += unquote(content)
    expected_sitemap = {origin + route for route, (_, indexable) in routes.items() if indexable}
    actual_sitemap = set(re.findall(r"<loc>(.*?)</loc>", sitemap))
    if strict_seongnam:
        assert actual_sitemap == expected_sitemap, f"Unexpected sitemap set: {actual_sitemap ^ expected_sitemap}"
    for route, (_, indexable) in routes.items():
        if not indexable: continue
        assert f"<loc>{origin}{route}</loc>" in sitemap, f"Missing sitemap route {route}"
    status, body, headers = response("/site-factory-live-qa-definitely-not-found/")
    assert status == 404 and "페이지를 찾을 수 없습니다" in body
    if strict_seongnam:
        not_found = Document(body)
        assert "noindex" in not_found.metas.get("robots", "").lower(), "404 missing noindex meta"
        assert not not_found.canonicals and "application/ld+json" not in body, "404 has canonical or product schema"
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
    parser.add_argument("--site-key", default="", help="Trusted registry key; Seongnam opts into its stricter release contract")
    parser.add_argument("--launch-key", default="")
    parser.add_argument("--scope-key", default="")
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--phase", choices=["preview", "production"], default="production")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--version-preview", action="store_true")
    parser.add_argument("--version-upload-result", type=Path)
    parser.add_argument("--protect-public", action="store_true")
    parser.add_argument("--probe-path", default="")
    args = parser.parse_args()
    assert re.fullmatch(r"[0-9a-f]{40}", args.revision), "Expected full pinned commit SHA"
    origin = args.origin.rstrip("/")
    if args.site_key == GOYANG_SITE:
        require(args.registry is not None and args.baseline_root is not None, "Goyang trusted registry and fixed baseline required")
        site = json.loads(args.registry.read_text())["sites"][GOYANG_SITE]
        target = resolve_goyang_coverage_target(site, "joseungil-kr/fwith-site-factory", args.revision,
            args.launch_key, args.scope_key, args.phase, args.version_preview)
        try:
            require(not args.version_preview or args.phase == "preview", "Version URLs are noindex-only")
            require(not args.version_upload_result or args.version_preview, "Upload result requires version preview")
            require(not args.protect_public or args.version_preview, "Public protection requires version path")
            reference = goyang_public_reference(site) if args.protect_public else {
                "revision": args.revision, "manifest_sha256": target["manifest_sha256"], "phase": args.phase}
            upload = read_goyang_version_upload(args.version_upload_result.read_text()) if args.version_upload_result else None
            require(args.validate_only or args.protect_public or not args.version_preview or upload,
                    "Live version verification requires actual upload result")
            fetch_origin = upload["previewUrl"] if upload and not args.protect_public else origin
            binary_fetch = goyang_http_fetch(fetch_origin)
            def text_fetch(route):
                status, body, headers = binary_fetch(route)
                return status, body.decode("utf-8"), headers
            result = verify_goyang_coverage(args.root, args.baseline_root, origin, reference["revision"],
                reference["manifest_sha256"], reference["phase"], None if args.validate_only else text_fetch,
                args.version_preview and not args.protect_public)
            if not args.validate_only and args.version_preview:
                result["verifiedAssets"] = verify_goyang_assets(args.root, binary_fetch, reference["phase"] == "preview")
                if args.protect_public:
                    verify_goyang_probe_absent(args.root, args.probe_path, binary_fetch)
                    result["publicArtifactPreserved"] = True
                else:
                    path = validate_goyang_probe_path(args.probe_path)
                    probe = (args.root / "dist" / path.lstrip("/"))
                    require(probe.is_file() and probe.read_text() == "site-factory-version-isolation " + args.revision + "\n", "Probe does not identify exact source")
                    result.update(upload, assetIsolationProbe=path)
        except PermissionError:
            result = {"pipelineState": "verification_blocked", "revision": args.revision, "reason": "Goyang HTTP403; verification remains blocked"}
        except (AssertionError, ValueError, KeyError, TypeError, OSError, ET.ParseError):
            result = {"pipelineState": "verification_failed", "revision": args.revision, "reason": "Goyang source/artifact/HTTP contract failed; no raw response is logged"}
        Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False))
        if result["pipelineState"] not in {"goyang_source_validated", "preview_verified", "live_verified"}:
            raise SystemExit(2)
        return
    require(not args.scope_key and not args.launch_key and not args.validate_only and args.phase == "production"
            and not args.version_preview and not args.version_upload_result and not args.protect_public and not args.probe_path,
            "Coverage-only options are not supported for other sites")
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
            result = verify(args.root, origin, args.revision, fetch, args.naver_verification, args.indexnow_key, args.site_key)
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
