#!/usr/bin/env python3
"""Fixed Goyang canonical/noindex QA; authenticated operations are GET-only."""
import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, urlopen

from goyang_domain import HOSTNAME, ZONE_NAME, WORKER, REVISION, SNAPSHOT, NoRedirect, PreflightError, pages, single_page
import verify_preview as preview

ORIGIN = "https://" + HOSTNAME
DETAIL = "/funeral/ilsan-paik-funeral-wreath/"
HUB = "/funeral/"


def check_binding(transport, account_id):
    if not isinstance(account_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
        raise PreflightError("invalid_account_configuration")
    zones = pages(transport, "/zones?" + urlencode({"name": ZONE_NAME, "status": "active", "account.id": account_id}))
    if (len(zones) != 1 or zones[0].get("name") != ZONE_NAME or zones[0].get("status") != "active"
            or not isinstance(zones[0].get("account"), dict) or zones[0]["account"].get("id") != account_id
            or not isinstance(zones[0].get("id"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", zones[0]["id"])):
        raise PreflightError("zone_scope_uncertain")
    domains = single_page(transport, f"/accounts/{account_id}/workers/domains?" + urlencode({"hostname": HOSTNAME}))
    expected = {"hostname": HOSTNAME, "service": WORKER, "zone_id": zones[0]["id"], "environment": "production"}
    if len(domains) != 1 or any(domains[0].get(key) != value for key, value in expected.items()):
        raise PreflightError("fixed_binding_mismatch")
    return {"state": "goyang_binding_verified", "hostname": HOSTNAME, "worker": WORKER}


def check_preview_capabilities(transport, account_id):
    """GET-only observation. No default-false inference and no upload/enable."""
    check_binding(transport, account_id)

    def read_object(path):
        try:
            payload = transport("GET", path)
        except HTTPError as error:
            raise PreflightError("capability_http_error", error.code) from None
        except Exception:
            raise PreflightError("capability_request_failed") from None
        if (not isinstance(payload, dict) or payload.get("success") is not True
                or payload.get("errors", []) != [] or not isinstance(payload.get("result"), dict)):
            raise PreflightError("capability_response_invalid")
        return payload

    prefix = f"/accounts/{account_id}/workers/scripts/{WORKER}"
    subdomain = read_object(prefix + "/subdomain")["result"]
    if any(type(subdomain.get(key)) is not bool for key in ("enabled", "previews_enabled")):
        raise PreflightError("preview_capability_not_observed")
    payload = read_object(prefix + "/deployments?page=1&per_page=1")
    deployments, info = payload["result"].get("deployments"), payload.get("result_info", {})
    # Cloudflare documents the first entry as the deployment serving traffic.
    # We ask for that one entry, not a supposedly complete history.
    if (not isinstance(deployments, list) or len(deployments) != 1 or not isinstance(deployments[0], dict)
            or not isinstance(info, dict) or info.get("page", 1) != 1
            or info.get("per_page", 1) != 1 or info.get("count", 1) != 1
            or any(key in info and type(info[key]) is not int for key in ("page", "per_page", "count"))):
        raise PreflightError("active_deployment_not_observed")
    deployment = deployments[0]
    uuid = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    if not isinstance(deployment.get("id"), str) or not re.fullmatch(uuid, deployment["id"]):
        raise PreflightError("active_deployment_invalid")
    return {"state": "goyang_preview_capabilities_observed", "hostname": HOSTNAME, "worker": WORKER,
            "previews_enabled": subdomain["previews_enabled"], "deployment_id": deployment["id"],
            "mutations_performed": False}



class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.canonicals, self.snapshots, self.hrefs = {}, [], [], []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag.lower() == "meta" and values.get("name"):
            self.meta[values["name"].lower()] = values.get("content", "")
        if tag.lower() == "link" and values.get("rel", "").lower() == "canonical":
            self.canonicals.append(values.get("href", ""))
        if tag.lower() == "article" and "data-snapshot-id" in values:
            self.snapshots.append(values["data-snapshot-id"])
        if tag.lower() == "a" and "href" in values:
            self.hrefs.append(values["href"])


def verify_http(opener=urlopen, sleeper=time.sleep):
    result = preview.verify(ORIGIN, REVISION, opener=opener, sleeper=sleeper)
    if result["state"] != "preview_verified":
        return result
    step = "home"
    try:
        for step, path in (("home", "/"), ("detail", DETAIL), ("funeral_hub", HUB)):
            request = Request(ORIGIN + path, headers={"User-Agent": "SiteFactory-StagingQA/3.0"})
            try:
                with opener(request, timeout=15) as response:
                    if response.status != 200 or response.geturl() != ORIGIN + path:
                        raise ValueError("https_route_mismatch")
                    text = response.read().decode("utf-8")
                    header = response.headers.get("X-Robots-Tag", "")
            except HTTPError as error:
                error.site_factory_step, error.site_factory_origin = step, ORIGIN
                raise
            page = PageParser()
            page.feed(text)
            if page.canonicals != [ORIGIN + path] or page.meta.get("site-factory-revision") != REVISION:
                raise ValueError("canonical_or_revision_mismatch")
            if "noindex" not in {part.strip().lower() for part in page.meta.get("robots", "").split(",")}:
                raise ValueError("noindex_meta_mismatch")
            if "noindex" not in {part.strip().lower() for part in header.split(",")}:
                raise ValueError("noindex_header_mismatch")
            if step == "detail" and page.snapshots != [SNAPSHOT]:
                raise ValueError("frozen_snapshot_mismatch")
            if step == "funeral_hub" and DETAIL not in page.hrefs:
                raise ValueError("hub_detail_link_mismatch")
        # Exact e4eead3 noindex build: one index/child, home + frozen detail.
        # The thin funeral hub is excluded; robots does not advertise a sitemap.
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        for step, path, tag, expected in (
            ("sitemap_index", "/sitemap-index.xml", "sitemapindex", {ORIGIN + "/sitemap-0.xml"}),
            ("sitemap_urls", "/sitemap-0.xml", "urlset", {ORIGIN + "/", ORIGIN + DETAIL}),
        ):
            request = Request(ORIGIN + path, headers={"User-Agent": "SiteFactory-StagingQA/3.0"})
            try:
                with opener(request, timeout=15) as response:
                    if response.status != 200 or response.geturl() != ORIGIN + path:
                        raise ValueError("https_sitemap_route_mismatch")
                    if "noindex" not in {part.strip().lower() for part in response.headers.get("X-Robots-Tag", "").split(",")}:
                        raise ValueError("sitemap_noindex_header_mismatch")
                    raw = response.read(1024 * 1024 + 1)
            except HTTPError as error:
                error.site_factory_step, error.site_factory_origin = step, ORIGIN
                raise
            text = raw.decode("utf-8")
            if len(raw) > 1024 * 1024 or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
                raise ValueError("unsafe_sitemap_xml")
            xml = ET.fromstring(text)
            locations = [node.text for node in xml.iter(namespace + "loc")]
            entry_tag = namespace + ("sitemap" if tag == "sitemapindex" else "url")
            if (xml.tag != namespace + tag or len(xml) != len(expected)
                    or any(entry.tag != entry_tag or len(entry.findall(namespace + "loc")) != 1 for entry in xml)
                    or len(locations) != len(expected) or set(locations) != expected):
                raise ValueError("sitemap_isolation_mismatch")
    except Exception as error:
        return {"state": "goyang_canonical_qa_failed", "step": step, "lastFailure": preview.describe_failure(error)}
    return {"state": "goyang_canonical_noindex_verified", "origin": ORIGIN, "revision": REVISION, "snapshot": SNAPSHOT,
            "sitemap": {"index": ORIGIN + "/sitemap-index.xml", "child": ORIGIN + "/sitemap-0.xml",
                        "urls": sorted({ORIGIN + "/", ORIGIN + DETAIL}), "noindexHeaderVerified": True}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("binding", "http", "preview-capabilities"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "http":
        result = verify_http()
    else:
        token, account = os.environ.get("CLOUDFLARE_API_TOKEN", ""), os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        opener = build_opener(NoRedirect())

        def transport(method, path):
            if method != "GET":
                raise RuntimeError("read_only")
            request = Request("https://api.cloudflare.com/client/v4" + path, method="GET", headers={"Authorization": "Bearer " + token})
            with opener.open(request, timeout=20) as response:
                payload = response.read(1024 * 1024 + 1)
            if len(payload) > 1024 * 1024:
                raise RuntimeError("response_limit")
            return json.loads(payload)

        try:
            if not token:
                raise PreflightError("missing_credentials")
            result = check_preview_capabilities(transport, account) if args.mode == "preview-capabilities" else check_binding(transport, account)
        except PreflightError as error:
            result = {"state": "goyang_preview_capabilities_blocked" if args.mode == "preview-capabilities" else "goyang_binding_failed", "code": error.code}
            if args.mode == "preview-capabilities":
                result.update(previews_enabled=None, deployment_id=None, mutations_performed=False)
            if error.status is not None:
                result["httpStatus"] = error.status
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result) if args.mode == "preview-capabilities" else result["state"])
    return int(result["state"] not in {"goyang_binding_verified", "goyang_canonical_noindex_verified", "goyang_preview_capabilities_observed"})


if __name__ == "__main__":
    raise SystemExit(main())
