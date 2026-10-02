#!/usr/bin/env python3
"""Read-only, fail-closed inspection of the fixed Goyang noindex hostname."""
import argparse
from datetime import datetime, timezone
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOSTNAME = "goyang.fwith.kr"
ZONE_NAME = "fwith.kr"
WORKER = "goyang-flower-guide-qa"
REVISION = "e4eead3e881b3b4c09a60e2af5befb55b6787413"
SNAPSHOT = "goyang-ilsan-paik-r2-20261002T040830"
PER_PAGE = 50


class PreflightError(RuntimeError):
    def __init__(self, code, status=None):
        super().__init__(code)
        self.code = code
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        self.report = None


def evidence():
    return {
        "hostname": HOSTNAME, "zone": ZONE_NAME, "worker": WORKER,
        "expectedRevision": REVISION, "expectedSnapshot": SNAPSHOT,
        "utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "applyEnabled": False, "state": "inspection_failed",
        "scope": "configured_account_and_exact_hostname",
        "coverage": {key: "not_observed" for key in ("zone", "domains", "dns", "routes")},
        "counts": {},
    }


def response(transport, path):
    try:
        data = transport("GET", path)
    except HTTPError as error:
        raise PreflightError("http_error", error.code) from None
    except Exception:
        raise PreflightError("request_failed") from None
    if not isinstance(data, dict) or data.get("success") is not True:
        raise PreflightError("api_failure")
    rows, info = data.get("result"), data.get("result_info", {})
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise PreflightError("malformed_response")
    if not isinstance(info, dict):
        raise PreflightError("malformed_response")
    for key in ("page", "per_page", "count", "total_count", "total_pages"):
        if key in info and (type(info[key]) is not int or info[key] < 0):
            raise PreflightError("malformed_pagination")
    return rows, info


def pages(transport, path):
    """Zones and DNS records are paginated; missing metadata is not completeness."""
    results, total = [], None
    for page in range(1, 1001):
        rows, info = response(transport, path + "&" + urlencode({"page": page, "per_page": PER_PAGE}))
        if not all(key in info for key in ("page", "per_page", "count", "total_count", "total_pages")):
            raise PreflightError("incomplete_pagination")
        count = info["total_count"]
        last = max(1, (count + PER_PAGE - 1) // PER_PAGE)
        if (info["page"] != page or info["per_page"] != PER_PAGE
                or info["count"] != len(rows) or len(rows) != min(PER_PAGE, max(0, count - (page - 1) * PER_PAGE))
                or info["total_pages"] not in ({0, 1} if count == 0 else {last})
                or (total is not None and count != total)):
            raise PreflightError("incomplete_pagination")
        total = count
        results.extend(rows)
        if page == last:
            return results
    raise PreflightError("pagination_limit")


def single_page(transport, path):
    """Workers Domains/Routes use SyncSinglePage; do not invent pagination."""
    rows, info = response(transport, path)
    if (info.get("page", 1) != 1
            or info.get("total_pages", 1) not in ({0, 1} if not rows else {1})
            or info.get("count", len(rows)) != len(rows)
            or info.get("total_count", len(rows)) != len(rows)
            or info.get("per_page", len(rows)) < len(rows)):
        raise PreflightError("incomplete_single_page")
    return rows


def overlaps(pattern):
    if not isinstance(pattern, str):
        raise PreflightError("malformed_route")
    value = pattern.lower()
    for prefix in ("http://", "https://"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    host, slash, _ = value.partition("/")
    if not slash or not re.fullmatch(r"[a-z0-9.*-]+", host) or ".." in host:
        raise PreflightError("malformed_route")
    return re.fullmatch(re.escape(host).replace(r"\*", ".*"), HOSTNAME) is not None


def inspect(transport, account_id):
    report, stage = evidence(), "configuration"
    try:
        if not isinstance(account_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
            raise PreflightError("invalid_account_configuration")
        stage = "zone"
        zones = pages(transport, "/zones?" + urlencode({"name": ZONE_NAME, "status": "active", "account.id": account_id}))
        if (len(zones) != 1 or zones[0].get("name") != ZONE_NAME or zones[0].get("status") != "active"
                or not isinstance(zones[0].get("account"), dict) or zones[0]["account"].get("id") != account_id
                or not isinstance(zones[0].get("id"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", zones[0]["id"])):
            raise PreflightError("zone_scope_uncertain")
        zone_id = zones[0]["id"]
        report["coverage"][stage], report["counts"]["zones"] = "complete", 1
        stage = "domains"
        domains = single_page(transport, f"/accounts/{account_id}/workers/domains?" + urlencode({"hostname": HOSTNAME}))
        if any(row.get("hostname") != HOSTNAME or not isinstance(row.get("service"), str)
               or not row["service"] or not isinstance(row.get("zone_id"), str) for row in domains):
            raise PreflightError("domain_scope_uncertain")
        report["coverage"][stage], report["counts"]["workerDomains"] = "complete", len(domains)
        report["domainBinding"] = ("none" if not domains else "same_worker" if len(domains) == 1
                                   and domains[0]["service"] == WORKER and domains[0]["zone_id"] == zone_id else "other_or_multiple")
        stage = "dns"
        records = pages(transport, f"/zones/{zone_id}/dns_records?" + urlencode({"name.exact": HOSTNAME}))
        if any(row.get("name") != HOSTNAME or not isinstance(row.get("type"), str) or not row["type"] for row in records):
            raise PreflightError("dns_scope_uncertain")
        report["coverage"][stage], report["counts"]["dnsRecords"] = "complete", len(records)
        stage = "routes"
        routes = single_page(transport, f"/zones/{zone_id}/workers/routes")
        collisions = sum(overlaps(row.get("pattern")) for row in routes)
        report["coverage"][stage] = "complete"
        report["counts"].update(workerRoutes=len(routes), overlappingWorkerRoutes=collisions)
        report.update(state="inspection_complete", collisionsObserved=bool(domains or records or collisions))
        return report
    except PreflightError as error:
        report["failure"] = {"stage": stage, "code": error.code}
        if error.status is not None:
            report["failure"]["httpStatus"] = error.status
        error.report = report
        raise


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    opener = build_opener(NoRedirect())

    def transport(method, path):
        if method != "GET":
            raise RuntimeError("read_only")
        request = Request("https://api.cloudflare.com/client/v4" + path, method="GET",
                          headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
        with opener.open(request, timeout=20) as result:
            body = result.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise RuntimeError("response_limit")
        return json.loads(body)

    try:
        if not token:
            error = PreflightError("missing_credentials")
            error.report = evidence()
            error.report["failure"] = {"stage": "configuration", "code": error.code}
            raise error
        report = inspect(transport, account_id)
    except PreflightError as error:
        report = error.report
    try:
        with open(args.output, "w", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    except OSError:
        print("Goyang inspection evidence could not be saved.")
        return 1
    print("Goyang inspection: " + report["state"] + "; apply disabled.")
    return int(report["state"] != "inspection_complete" or report["collisionsObserved"])


if __name__ == "__main__":
    raise SystemExit(main())
