#!/usr/bin/env python3
"""Request the fixed Seongnam Custom Domain with server-side overrides disabled.

Uses the native Custom Domains endpoint used by Wrangler 4.147.0. No separate
DNS/routes inventory, force, retry or alternate endpoint is used. A successful
request is not live verification; the production controller verifies HTTP next.
"""
import argparse
import json
import os
import re
from urllib.error import HTTPError
from urllib.request import Request, build_opener

from seongnam_domain import HOSTNAME, ZONE_NAME, WORKER, NoRedirect, PreflightError


def error_codes(payload):
    """Return only bounded integer Cloudflare codes, never upstream messages."""
    rows = payload.get("errors") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    return sorted({row["code"] for row in rows[:20]
                   if isinstance(row, dict) and type(row.get("code")) is int
                   and 0 <= row["code"] <= 1000000000})[:5]


def failure(code, status=None, codes=()):
    error = PreflightError(code, status)
    error.cloudflare_codes = list(codes)
    return error


def attach(transport, account_id):
    if not isinstance(account_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
        raise failure("invalid_account_configuration")
    # Official implementation and option contract:
    # cloudflare/workers-sdk tag wrangler@4.147.0,
    # packages/deploy-helpers/src/triggers/publish-routes.ts, publishCustomDomains.
    # Never inherit Wrangler's non-TTY auto-override defaults.
    endpoint = f"/accounts/{account_id}/workers/scripts/{WORKER}/domains/records"
    body = {
        "override_scope": False,
        "override_existing_origin": False,
        "override_existing_dns_record": False,
        "origins": [{"hostname": HOSTNAME, "zone_name": ZONE_NAME}],
    }
    try:
        result = transport("PUT", endpoint, body)
    except HTTPError as error:
        codes = []
        try:
            raw = error.read(8193)
            if len(raw) <= 8192:
                codes = error_codes(json.loads(raw))
        except Exception:
            pass
        finally:
            error.close()
        uncertain = error.code == 408 or (type(error.code) is int and error.code >= 500)
        raise failure("attach_result_uncertain" if uncertain else "attach_http_error", error.code, codes) from None
    except Exception:
        # The server may have applied a timed-out request. Never replay it here.
        raise failure("attach_result_uncertain") from None
    if not isinstance(result, dict) or result.get("success") is not True:
        raise failure("attach_api_failure", codes=error_codes(result))
    return "request_accepted"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not token:
        print("Seongnam domain request failed: missing_credentials")
        return 1
    opener = build_opener(NoRedirect())

    def transport(method, path, body=None):
        expected = f"/accounts/{account_id}/workers/scripts/{WORKER}/domains/records"
        if method != "PUT" or path != expected:
            raise RuntimeError("operation_not_allowed")
        request = Request("https://api.cloudflare.com/client/v4" + path, method="PUT",
                          data=json.dumps(body).encode(),
                          headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with opener.open(request, timeout=20) as response:
            payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise RuntimeError("response_limit")
        return json.loads(payload)

    try:
        state = attach(transport, account_id)
    except PreflightError as error:
        print("Seongnam domain request failed: " + error.code
              + (f" HTTP {error.status}" if error.status is not None else "")
              + "; stage=native_custom_domain_put; cloudflareErrorCodes="
              + json.dumps(getattr(error, "cloudflare_codes", [])))
        return 1
    print("Seongnam hostname: " + HOSTNAME + "; " + state + "; live verification pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
