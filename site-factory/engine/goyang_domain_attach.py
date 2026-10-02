#!/usr/bin/env python3
"""Attach only the fixed hostname to the existing QA Worker; never deploy assets."""
import argparse
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from goyang_domain import HOSTNAME, ZONE_NAME, WORKER, NoRedirect, PreflightError, pages, single_page


def attach(transport, account_id, *, operator_confirmed_unused=False):
    if operator_confirmed_unused is not True:
        raise PreflightError("operator_confirmation_required")
    if not isinstance(account_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
        raise PreflightError("invalid_account_configuration")
    zones = pages(transport, "/zones?" + urlencode({"name": ZONE_NAME, "status": "active", "account.id": account_id}))
    if (len(zones) != 1 or zones[0].get("name") != ZONE_NAME or zones[0].get("status") != "active"
            or not isinstance(zones[0].get("account"), dict) or zones[0]["account"].get("id") != account_id
            or not isinstance(zones[0].get("id"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", zones[0]["id"])):
        raise PreflightError("zone_scope_uncertain")
    zone_id = zones[0]["id"]
    endpoint = f"/accounts/{account_id}/workers/domains"
    lookup = endpoint + "?" + urlencode({"hostname": HOSTNAME})
    # Current API request schema omits environment; the legacy response must be production.
    body = {"hostname": HOSTNAME, "service": WORKER, "zone_id": zone_id}

    def same_binding(rows):
        return len(rows) == 1 and all(rows[0].get(key) == value for key, value in body.items()) and rows[0].get("environment") == "production"

    existing = single_page(transport, lookup)
    if existing:
        if same_binding(existing):
            return "already_attached"
        raise PreflightError("hostname_binding_conflict")
    # The operator confirmed this fixed hostname unused. Do not retry denied DNS reads.
    uncertain = False
    try:
        result = transport("PUT", endpoint, body)
    except HTTPError as error:
        if type(error.code) is int and 400 <= error.code < 500 and error.code != 408:
            raise PreflightError("attach_http_error", error.code) from None
        uncertain = True
    except Exception:
        uncertain = True
    if not uncertain and (not isinstance(result, dict) or result.get("success") is not True):
        raise PreflightError("attach_api_failure")
    try:
        readback = single_page(transport, lookup)
    except PreflightError as error:
        raise PreflightError("attach_readback_uncertain", error.status) from None
    if not same_binding(readback):
        raise PreflightError("attach_readback_uncertain")
    return "attached_after_uncertain_response" if uncertain else "attached"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-confirmed-unused", action="store_true")
    args = parser.parse_args(argv)
    if not args.operator_confirmed_unused:
        print("Goyang attach failed: operator_confirmation_required")
        return 1
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not token:
        print("Goyang attach failed: missing_credentials")
        return 1
    opener = build_opener(NoRedirect())

    def transport(method, path, body=None):
        if method not in ("GET", "PUT") or (method == "PUT" and path != f"/accounts/{account_id}/workers/domains"):
            raise RuntimeError("operation_not_allowed")
        request = Request("https://api.cloudflare.com/client/v4" + path, method=method,
                          data=None if body is None else json.dumps(body).encode(),
                          headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with opener.open(request, timeout=20) as response:
            payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise RuntimeError("response_limit")
        return json.loads(payload)

    try:
        state = attach(transport, account_id, operator_confirmed_unused=args.operator_confirmed_unused)
    except PreflightError as error:
        print("Goyang attach failed: " + error.code + (f" HTTP {error.status}" if error.status is not None else ""))
        return 1
    print("Goyang hostname: " + HOSTNAME + "; " + state + "; assets unchanged; canonical follow-up pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
