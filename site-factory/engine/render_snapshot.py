#!/usr/bin/env python3
"""Validate a frozen queue payload and render the registered site's actual input.

No network, model calls or publication occur here. All validation finishes before
any file is replaced; Git/CI provide the transaction boundary for the file set.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse


class SnapshotError(ValueError):
    pass


def fail(message):
    raise SnapshotError(message)


def identifier(value, label):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", value):
        fail(f"Unsafe {label}: expected an alphanumeric identifier (no paths/newlines)")
    return value


def parse_payload(body):
    # Headers may only precede content blocks; customer copy cannot override them.
    header = body.split("---BEGIN-", 1)[0]
    values = {}
    for line in header.splitlines():
        match = re.fullmatch(r"([A-Z][A-Z0-9_]*): (.*)", line)
        if match:
            key, value = match.groups()
            if key in values:
                fail(f"Duplicate header: {key}")
            values[key] = value.strip()

    def required(key):
        value = values.get(key, "")
        if not value:
            fail(f"Missing {key}; repair the frozen queue payload before retrying")
        return value

    def block(key, required=False):
        begin, end = f"---BEGIN-{key}---", f"---END-{key}---"
        count = body.count(begin), body.count(end)
        if count == (0, 0) and not required:
            return ""
        if count != (1, 1) or body.index(begin) >= body.index(end):
            fail(f"Missing or ambiguous block: {key}")
        return body.split(begin, 1)[1].split(end, 1)[0].strip()

    for key in ("PUBLISH_QUEUE_RECORD_ID", "SITE_KEY", "PAGE_KEY", "DRAFT_KEY", "SOURCE_RECORD_ID", "SNAPSHOT_ID", "TARGET_REPO", "TARGET_BRANCH", "TARGET_ROOT", "SLUG", "CATEGORY", "STRUCTURE_TYPE", "PAGE_TYPE", "LOCALIZATION_POLICY", "REGION", "VERIFIED_AT"):
        required(key)
    for key in ("PAGE_KEY", "DRAFT_KEY", "SNAPSHOT_ID", "SITE_KEY", "STRUCTURE_TYPE"):
        identifier(values[key], key)
    for key in ("PUBLISH_QUEUE_RECORD_ID", "SOURCE_RECORD_ID"):
        if not re.fullmatch(r"rec[A-Za-z0-9]{14}", values[key]):
            fail(f"Invalid Airtable identifier: {key}")
    for key in ("TITLE", "DESCRIPTION", "CONTENT", "SOURCES"):
        values[key] = block(key, required=True)
        if not values[key]:
            fail(f"Empty required block: {key}")
    for key in ("SOURCE-NAMES", "SOURCE-TYPES", "RELATED-PAGE-KEYS", "CARD-SUMMARY", "FIRST-ANSWER"):
        values[key] = block(key)
    return values


def validate_content(p):
    slug = p["SLUG"]
    if not slug or len(slug) > 80 or not all(c.isalnum() or c == "-" for c in slug):
        fail("Unsafe SLUG: only Unicode letters, numbers and hyphens are allowed")
    p["ROUTE_TYPE"] = p.get("ROUTE_TYPE", "category")
    if p["ROUTE_TYPE"] not in {"category", "top_level"}:
        fail("Unsupported ROUTE_TYPE")
    if p["LOCALIZATION_POLICY"] not in {"local-required", "local-optional", "global"}:
        fail("Unsupported LOCALIZATION_POLICY")
    p["CONTENT_ROLE"] = p.get("CONTENT_ROLE") or ("informational-pillar" if p["ROUTE_TYPE"] == "top_level" else "question-answer")
    if p["CONTENT_ROLE"] not in {"informational-pillar", "question-answer"}:
        fail("Unsupported CONTENT_ROLE")
    try:
        date = dt.date.fromisoformat(p["VERIFIED_AT"][:10])
    except ValueError:
        fail("VERIFIED_AT must be a real ISO date")
    if date > dt.datetime.now(dt.timezone.utc).date():
        fail("VERIFIED_AT cannot be in the future")
    p["VERIFIED_AT"] = date.isoformat()
    for key in ("TITLE", "DESCRIPTION", "H1"):
        if not p.get(key):
            continue
        if "\n" in p[key] or "\r" in p[key] or "<" in p[key] or "\x00" in p[key]:
            fail(f"{key} must be plain single-line text")
    content = p["CONTENT"].replace("\r\n", "\n")
    content = re.sub(r"\A#\s+[^\n]+\n*", "", content).strip()
    if re.search(r"(?m)^#\s+", content):
        fail("CONTENT must not contain H1; the page renderer owns the single H1")
    if re.search(r"<\s*/?\s*[A-Za-z!]|javascript:|data:text/html", content, re.I):
        fail("Raw HTML and executable URLs are forbidden in snapshot Markdown")
    if len(content) < 160:
        fail("CONTENT is too short to answer a customer query")
    p["CONTENT"] = content
    p["PRIMARY_KEYWORD"] = p.get("PRIMARY_KEYWORD") or p["TITLE"].split("|")[0].strip()
    keyword = re.sub(r"\s+", "", p["PRIMARY_KEYWORD"])
    if keyword not in re.sub(r"\s+", "", p["TITLE"].split("|")[0]):
        fail("Title must preserve PRIMARY_KEYWORD in its opening phrase")
    sources = p["SOURCES"].splitlines()
    names, types = p["SOURCE-NAMES"].splitlines(), p["SOURCE-TYPES"].splitlines()
    p["sources"] = []
    for i, url in enumerate(sources):
        parsed = urlparse(url.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            fail("Every source must be a public HTTPS URL without credentials")
        typ = types[i].strip() if i < len(types) else "reference"
        if typ not in {"official", "business", "facility", "education", "professional", "reference"}:
            fail(f"Unsupported source type: {typ}")
        p["sources"].append({"name": names[i].strip() if i < len(names) else parsed.hostname, "url": url.strip(), "type": typ, "verifiedAt": p["VERIFIED_AT"]})
    p["relatedKeys"] = [identifier(k.strip(), "RELATED-PAGE-KEYS") for k in p["RELATED-PAGE-KEYS"].splitlines() if k.strip()]
    p["url"] = f'/{slug}/' if p["ROUTE_TYPE"] == "top_level" else f'/{p["CATEGORY"]}/{slug}/'
    role = p.get("PAGE_ROLE") or ("REGION_SERVICE_LANDING" if p["ROUTE_TYPE"] == "top_level" else "PRICE_GUIDE" if p["PAGE_TYPE"] == "price-guide" else "PLACE_LANDING" if p["PAGE_TYPE"] in {"funeral-facility", "hospital", "hospital-visit", "station-transit", "event-venue"} else "INTENT_LANDING")
    if role not in {"REGION_SERVICE_LANDING", "PLACE_LANDING", "INTENT_LANDING", "PRICE_GUIDE", "INFORMATION_GUIDE"}:
        fail("Unsupported PAGE_ROLE")
    p["PAGE_ROLE"] = role
    p["PARENT_HUB"] = p.get("PARENT_HUB") or ("/" if p["ROUTE_TYPE"] == "top_level" else f'/{p["CATEGORY"]}/')
    if p["PARENT_HUB"] != ("/" if p["ROUTE_TYPE"] == "top_level" else f'/{p["CATEGORY"]}/'):
        fail("PARENT_HUB must match the registered route category")
    p["INTENT_KEY"] = p.get("INTENT_KEY") or f'{p["REGION"]}|{role}|{p["PRIMARY_KEYWORD"]}'
    return p


def load_json(path, default=None):
    if not path.exists():
        if default is not None:
            return default
        fail(f"Missing snapshot baseline: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def keyed(document, label):
    rows = document.get("pages", []) if isinstance(document, dict) else document
    result = {}
    for row in rows:
        key = row.get("pageKey")
        if not key or key in result:
            fail(f"Invalid or duplicate pageKey in {label}: {key}")
        result[key] = row
    return result


def frozen_hashes(p):
    # Airtable allocates the queue record ID only on creation. Review proof is
    # calculated before that trigger and binds every other frozen field; the
    # immutable storage hash additionally binds the allocated queue identity.
    canonical = {k: v for k, v in p.items() if k not in {"APPROVAL_STATUS", "APPROVED_SNAPSHOT_HASH"} and v != ""}
    encode = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    snapshot = hashlib.sha256(encode(canonical)).hexdigest()
    reviewed = {k: v for k, v in canonical.items() if k != "PUBLISH_QUEUE_RECORD_ID"}
    return snapshot, hashlib.sha256(encode(reviewed)).hexdigest()


def render(body, registry, workspace):
    p = validate_content(parse_payload(body))
    target = registry.get("sites", {}).get(p["SITE_KEY"])
    if not target:
        fail("Unregistered SITE_KEY")
    for key, field in (("TARGET_REPO", "repo"), ("TARGET_BRANCH", "branch"), ("TARGET_ROOT", "root")):
        if p[key] != target[field]:
            fail(f"{key} disagrees with the control registry")
    if p["CATEGORY"] not in target.get("allowedCategories", []) or p["PAGE_TYPE"] not in target.get("allowedPageTypes", []):
        fail("Category/page type is not allowed by this site's Blueprint")
    pairs = target.get("categoryPageTypes")
    if pairs is not None and p["PAGE_TYPE"] not in pairs.get(p["CATEGORY"], []):
        fail("Category/page type pair contradicts the registered Blueprint")
    workspace = Path(workspace).resolve()
    root = (workspace / target["root"]).resolve()
    if not root.is_relative_to(workspace) or root == workspace:
        fail("Registered root escapes the checkout")
    data = root / "src/data"
    manifest = load_json(data / "publish-manifest.json")
    page_map = load_json(data / "page-map.json")
    arch = load_json(data / "architecture.json", {"schemaVersion": 1, "siteKey": p["SITE_KEY"], "pages": []})
    tables = {"manifest": keyed(manifest, "manifest"), "map": keyed(page_map, "map"), "architecture": keyed(arch, "architecture")}
    renderer = target.get("snapshotRenderer", "markdown-v1")
    if renderer not in {"markdown-v1", "structured-json-v12"}:
        fail("Unknown registered snapshotRenderer; no implicit format guessing")
    pages = load_json(data / "pages.json") if renderer == "structured-json-v12" else None
    if pages is not None:
        tables["renderer"] = keyed(pages, "pages.json")
    content_keys = set(tables["manifest"])
    for name, table in tables.items():
        if name == "architecture" and renderer == "markdown-v1":
            # Preserve explicit redirect/merge history and a separate home
            # landing record used by legacy flower-local-v2 sites.
            extra = [row for k, row in table.items() if k not in content_keys]
            if not content_keys.issubset(table) or any(not (
                row.get("status") == "merged" and row.get("sitemapIndexable") is False
                or row.get("url") == "/" and row.get("pageRole") == "REGION_SERVICE_LANDING"
            ) for row in extra):
                fail("Unexplained architecture/manifest parity mismatch")
        elif set(table) != content_keys:
            fail("Existing renderer/manifest/map/architecture pageKey parity is broken")
    key = p["PAGE_KEY"]
    normalized = lambda value: re.sub(r"[\s|·?？:]+", "", value or "").casefold()
    for table in tables.values():
        for existing_key, row in table.items():
            if existing_key != key and (
                row.get("url") == p["url"] or row.get("intentKey") == p["INTENT_KEY"]
                or normalized(row.get("primaryKeyword")) == normalized(p["PRIMARY_KEYWORD"])
                or normalized(row.get("title")) == normalized(p["TITLE"])
            ):
                fail(f"URL/title/keyword/intent collision with {existing_key}")
    if any(k not in tables["manifest"] and k != key for k in p["relatedKeys"]):
        fail("RELATED-PAGE-KEYS contains an unknown target")
    digest, approval_digest = frozen_hashes(p)
    approval = p.get("APPROVAL_STATUS") == "approved" and p.get("APPROVED_SNAPSHOT_HASH") == approval_digest
    if p.get("APPROVED_SNAPSHOT_HASH") and not approval:
        fail("Approval status/hash does not match the exact frozen snapshot")
    require_approval = target.get("requireSnapshotApproval", renderer != "markdown-v1")
    publication_approved = approval or not require_approval
    ledger = dict(manifest.get("snapshotLedger", {}))
    for row in tables["manifest"].values():
        if row.get("snapshotId"):
            ledger.setdefault(row["snapshotId"], {"pageKey": row["pageKey"], "snapshotHash": row.get("snapshotHash"), "publishQueueRecordId": row.get("publishQueueRecordId")})
    for snapshot_id, frozen in ledger.items():
        if snapshot_id == p["SNAPSHOT_ID"] and frozen["pageKey"] != key:
            fail("SNAPSHOT_ID is already bound to another page")
        if frozen.get("publishQueueRecordId") == p["PUBLISH_QUEUE_RECORD_ID"] and snapshot_id != p["SNAPSHOT_ID"]:
            fail("PUBLISH_QUEUE_RECORD_ID is already bound to another immutable snapshot")
    known = ledger.get(p["SNAPSHOT_ID"])
    if known and known.get("snapshotHash") and known["snapshotHash"] != digest:
        fail("Historical immutable SNAPSHOT_ID reused with different content")
    prior = tables["manifest"].get(key)
    if prior:
        if prior["url"] != p["url"]:
            fail("Changing a published URL requires an explicit redirect migration")
        if prior.get("snapshotId") == p["SNAPSHOT_ID"]:
            if not prior.get("snapshotHash"):
                fail("Legacy snapshot has no immutable hash; use a new SNAPSHOT_ID and explicit SUPERSEDES_SNAPSHOT_ID")
            if prior["snapshotHash"] != digest:
                fail("Immutable SNAPSHOT_ID reused with different content")
        elif p.get("SUPERSEDES_SNAPSHOT_ID") != prior.get("snapshotId"):
            fail("Replacing a page requires SUPERSEDES_SNAPSHOT_ID matching its current snapshot")
    entry = {"pageKey": key, "snapshotId": p["SNAPSHOT_ID"], "snapshotHash": digest, "approvalVerified": approval, "draftKey": p["DRAFT_KEY"], "sourceRecordId": p["SOURCE_RECORD_ID"], "publishQueueRecordId": p["PUBLISH_QUEUE_RECORD_ID"], "slug": p["SLUG"], "category": p["CATEGORY"], "routeType": p["ROUTE_TYPE"], "url": p["url"], "title": p["TITLE"], "primaryKeyword": p["PRIMARY_KEYWORD"], "pageType": p["PAGE_TYPE"], "status": "approved"}
    writes = {}
    if renderer == "structured-json-v12":
        if p["ROUTE_TYPE"] != "category":
            fail("structured-json-v12 renders home separately; detail pages require category routes")
        summary = p.get("CARD-SUMMARY") or p["DESCRIPTION"]
        if summary.startswith(p["PRIMARY_KEYWORD"]):
            # Legacy Publisher has no card-summary slot. Keep its useful customer
            # benefit clause, rather than duplicating the opening keyword/title.
            summary = summary[len(p["PRIMARY_KEYWORD"]):].lstrip(" ,·|:은는을를")
        if not summary:
            fail("Snapshot needs a useful summary distinct from its keyword")
        first = p.get("FIRST-ANSWER") or re.split(r"\n\s*\n", p["CONTENT"], maxsplit=1)[0]
        if first.startswith("#"):
            fail("FIRST-ANSWER must be a direct plain-text customer answer")
        entry["file"] = "src/data/pages.json"
        old = tables["renderer"].get(key, {})
        page = {**old, **entry, "order": old.get("order", max([r.get("order", 0) for r in pages] + [0]) + 1), "h1": p.get("H1") or p["PRIMARY_KEYWORD"], "description": p["DESCRIPTION"], "cardSummary": summary, "firstAnswer": first, "contentMarkdown": p["CONTENT"], "sections": [], "faq": [], "sources": p["sources"], "source": p["sources"][0], "relatedKeys": p["relatedKeys"], "queryClass": p.get("QUERY_CLASS") or "support-info", "visualIntent": p.get("VISUAL_INTENT") or "consultation", "assetSlot": p.get("ASSET_SLOT") or "NONE"}
        tables["renderer"][key] = page
        writes[data / "pages.json"] = list(sorted(tables["renderer"].values(), key=lambda r: (r.get("order", 0), r["pageKey"])))
    else:
        entry["file"] = f"src/content/articles/{key}.md"
        legacy_sources = [{**s, "type": "reference" if s["type"] == "business" else s["type"]} for s in p["sources"]]
        fields = {"pageKey": key, "snapshotId": p["SNAPSHOT_ID"], "sourceDraftKey": p["DRAFT_KEY"], "sourceRecordId": p["SOURCE_RECORD_ID"], "slug": p["SLUG"], "routeType": p["ROUTE_TYPE"], "title": p["TITLE"], "description": p["DESCRIPTION"], "category": p["CATEGORY"], "structureType": p["STRUCTURE_TYPE"], "pageType": p["PAGE_TYPE"], "contentRole": p["CONTENT_ROLE"], "localizationPolicy": p["LOCALIZATION_POLICY"], "region": p["REGION"], "verifiedAt": p["VERIFIED_AT"], "sourceUrls": [s["url"] for s in p["sources"]], "sources": legacy_sources, "relatedPageKeys": p["relatedKeys"], "draftStatus": "approved"}
        # Emit only supplied review fields, preserving byte-identical legacy
        # snapshots when the optional Publisher slots are absent or blank.
        for header, field in (("H1", "h1"), ("CARD-SUMMARY", "cardSummary"),
                              ("FIRST-ANSWER", "firstAnswer"), ("QUERY_CLASS", "queryClass"),
                              ("VISUAL_INTENT", "visualIntent"), ("ASSET_SLOT", "assetSlot")):
            if p.get(header):
                fields[field] = p[header]
        # JSON values are valid YAML scalars/collections and cannot inject keys.
        article = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fields.items()) + "\n---\n\n" + p["CONTENT"] + "\n"
        writes[root / entry["file"]] = article
    tables["manifest"][key] = entry
    ledger[p["SNAPSHOT_ID"]] = {"pageKey": key, "snapshotHash": digest, "publishQueueRecordId": p["PUBLISH_QUEUE_RECORD_ID"]}
    manifest["snapshotLedger"] = ledger
    tables["map"][key] = dict(entry)
    tables["architecture"][key] = {**entry, "pageRole": p["PAGE_ROLE"], "parentHub": p["PARENT_HUB"], "intentKey": p["INTENT_KEY"], "contentRole": p["CONTENT_ROLE"], "localizationPolicy": p["LOCALIZATION_POLICY"], "sitemapIndexable": bool(target.get("productionEnabled")), "status": "primary"}
    for name, doc, filename in (("manifest", manifest, "publish-manifest.json"), ("map", page_map, "page-map.json"), ("architecture", arch, "architecture.json")):
        doc.update({"siteKey": p["SITE_KEY"], "pages": sorted(tables[name].values(), key=lambda r: r["pageKey"])})
        if name != "architecture":
            doc.update({"schemaVersion": 2, "generatedFrom": "Airtable Publish Queue", "snapshotMode": "git-frozen"})
        writes[data / filename] = doc
    for hub in arch.get("hubs", []):
        hub["children"] = sum(r.get("parentHub") == hub.get("url") for r in tables["architecture"].values())
    # Validate every destination including symlink resolution before any writes.
    for path in writes:
        if not path.resolve().is_relative_to(root):
            fail("Artifact path escapes the registered site root")
    changed = []
    pending = []
    for path, value in writes.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        temporary = path.with_suffix(path.suffix + ".snapshot-tmp")
        pending.append((path, temporary, path.read_bytes() if path.exists() else None, text))
    # Stage every byte first. If replacement fails, restore the entire file set.
    applied = []
    try:
        for path, temporary, previous, text in pending:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(text, encoding="utf-8")
        for path, temporary, previous, text in pending:
            temporary.replace(path)
            applied.append((path, previous))
            changed.append(str(path.relative_to(workspace)))
    except OSError:
        for path, previous in reversed(applied):
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous)
        raise
    finally:
        for path, temporary, previous, text in pending:
            temporary.unlink(missing_ok=True)
    return {"pipelineState": "rendered", "siteKey": p["SITE_KEY"], "pageKey": key, "snapshotId": p["SNAPSHOT_ID"], "snapshotHash": digest, "approvalHash": approval_digest, "approvalVerified": approval, "publicationApproved": publication_approved, "approvalMode": "explicit-hash" if approval else "required-preview-only" if require_approval else "legacy-trusted-writer", "renderer": renderer, "url": p["url"], "changedFiles": changed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--payload")
    args = parser.parse_args()
    body = Path(args.payload).read_text(encoding="utf-8") if args.payload else os.environ.get("ISSUE_BODY", "")
    try:
        result = render(body, load_json(Path(args.registry)), args.workspace)
    except (SnapshotError, json.JSONDecodeError) as error:
        raise SystemExit(f"SNAPSHOT VALIDATION FAILED: {error}")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
