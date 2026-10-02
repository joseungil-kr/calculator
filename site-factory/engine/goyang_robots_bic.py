#!/usr/bin/env python3
"""One approved BIC exception for the fixed Goyang /robots.txt request."""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from goyang_domain import HOSTNAME, ZONE_NAME, NoRedirect, PreflightError, pages

PHASE = "http_config_settings"
RULE = {
    "expression": '(http.host eq "goyang.fwith.kr" and http.request.uri.path eq "/robots.txt")',
    "action": "set_config", "action_parameters": {"bic": False}, "enabled": True,
}


def exact_rule(row):
    return (row.get("expression") == RULE["expression"] and row.get("action") == "set_config"
            and row.get("action_parameters") == {"bic": False}
            and row.get("action_parameters", {}).get("bic") is False and row.get("enabled") is True)


def entrypoint(transport, path):
    try:
        data = transport("GET", path)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise PreflightError("entrypoint_http_error", error.code) from None
    except Exception:
        raise PreflightError("entrypoint_request_failed") from None
    if not isinstance(data, dict) or data.get("success") is not True:
        raise PreflightError("entrypoint_api_failure")
    result = data.get("result")
    if (not isinstance(result, dict) or result.get("kind") != "zone" or result.get("phase") != PHASE
            or not isinstance(result.get("id"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", result["id"])
            or not isinstance(result.get("rules"), list) or any(not isinstance(row, dict) for row in result["rules"])):
        raise PreflightError("entrypoint_scope_uncertain")
    return result


def protected_rules(rows):
    keys = ("id", "expression", "action", "action_parameters", "enabled", "description", "ref")
    return [{key: row.get(key) for key in keys} for row in rows]


def apply_exception(transport, account_id):
    stage, wrote = "zone_read", False
    try:
        if not isinstance(account_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
            raise PreflightError("invalid_account_configuration")
        zones = pages(transport, "/zones?" + urlencode({"name": ZONE_NAME, "status": "active", "account.id": account_id}))
        if (len(zones) != 1 or zones[0].get("name") != ZONE_NAME or zones[0].get("status") != "active"
                or not isinstance(zones[0].get("account"), dict) or zones[0]["account"].get("id") != account_id
                or not isinstance(zones[0].get("id"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", zones[0]["id"])):
            raise PreflightError("zone_scope_uncertain")
        base = f"/zones/{zones[0]['id']}/rulesets"
        lookup = base + f"/phases/{PHASE}/entrypoint"
        stage = "entrypoint_read"
        before = entrypoint(transport, lookup)
        existing = before["rules"] if before is not None else []
        if any(exact_rule(row) for row in existing):
            if not exact_rule(existing[-1]):
                raise PreflightError("existing_rule_order_uncertain")
            return {"state": "bic_exception_already_present", "writeAttempted": False}
        baseline = protected_rules(existing)
        if before is None:
            stage, path = "create_entrypoint", base
            body = {"name": "Goyang robots BIC exception", "kind": "zone", "phase": PHASE, "rules": [RULE]}
        else:
            stage, path, body = "append_rule", base + f"/{before['id']}/rules", RULE
        wrote, uncertain = True, False
        try:
            result = transport("POST", path, body)
        except HTTPError as error:
            if type(error.code) is int and 400 <= error.code < 500 and error.code != 408:
                raise PreflightError("write_http_error", error.code) from None
            uncertain = True
        except Exception:
            uncertain = True
        if not uncertain:
            if isinstance(result, dict) and result.get("success") is False:
                raise PreflightError("write_api_rejected")
            uncertain = not isinstance(result, dict) or result.get("success") is not True
        stage = "write_readback"
        after = entrypoint(transport, lookup)
        if (after is None or (before is not None and after["id"] != before["id"])
                or len(after["rules"]) != len(existing) + 1
                or protected_rules(after["rules"][:-1]) != baseline or not exact_rule(after["rules"][-1])):
            raise PreflightError("write_readback_uncertain")
        return {"state": "bic_exception_added_after_uncertain_response" if uncertain else "bic_exception_added",
                "writeAttempted": True, "existingRulesPreserved": True}
    except PreflightError as error:
        error.stage, error.write_attempted = stage, wrote
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    token, account = os.environ.get("CLOUDFLARE_API_TOKEN", ""), os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    opener = build_opener(NoRedirect())

    def transport(method, path, body=None):
        if method not in ("GET", "POST"):
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
        if not token:
            raise PreflightError("missing_credentials")
        result = apply_exception(transport, account)
    except PreflightError as error:
        result = {"state": "bic_exception_failed", "stage": getattr(error, "stage", "configuration"),
                  "code": error.code, "writeAttempted": getattr(error, "write_attempted", False)}
        if error.status is not None:
            result["httpStatus"] = error.status
    result.update(hostname=HOSTNAME, path="/robots.txt", phase=PHASE, requiredPermission="Zone > Config Rules > Edit")
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return int(result["state"] == "bic_exception_failed")


if __name__ == "__main__":
    raise SystemExit(main())
