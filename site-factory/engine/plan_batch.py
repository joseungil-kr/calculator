#!/usr/bin/env python3
"""Query-first launch/growth selection for the existing external generators.

This adapter never invents business facts or starts a schedule. Airtable/agents
provide researched Blueprint, fingerprint and query candidates as JSON input.
"""
import argparse
import json
from pathlib import Path

PRIORITY = {"core-commercial": 0, "commercial-modifier": 1, "work-commercial": 2, "local-commercial": 3, "place-commercial": 3, "support-info": 4}
BLUEPRINT_FIELDS = ("blueprintKey", "services", "pageTypes", "queryPatterns", "forbiddenClaims", "sourcePriority", "requiredOrderInputs", "assetContract")
FINGERPRINT_FIELDS = ("brandKey", "brand", "conversionChannels")


def plan(data, mode, volume=None):
    blueprint, fingerprint = data.get("blueprint", {}), data.get("fingerprint", {})
    questions = []
    for field in BLUEPRINT_FIELDS:
        if field not in blueprint or blueprint[field] in (None, "", []):
            questions.append({"scope": "blueprint", "field": field})
    for field in FINGERPRINT_FIELDS:
        if not fingerprint.get(field):
            questions.append({"scope": "business", "field": field})
    if questions: return {"state": "bootstrap_required", "questions": questions, "selected": []}
    for channel in fingerprint["conversionChannels"]:
        if channel.get("sourceLevel") not in {"operator_confirmed", "official_business_source"} or not channel.get("value"):
            raise ValueError("Production conversion channels require verified business facts")
    for fact in fingerprint.get("facts", []):
        if fact.get("sourceLevel") not in {"operator_confirmed", "official_business_source", "industry_default", "unknown"}:
            raise ValueError("Unsupported truth sourceLevel")
        if fact.get("sourceLevel") == "official_business_source" and not fact.get("sourceUrls"):
            raise ValueError("Official business facts require source provenance")
    policy = data.get("policy", {})
    if mode == "growth" and policy.get("growthPaused", True):
        return {"state": "paused", "mode": mode, "selected": [], "reason": "Growth has not been explicitly resumed"}
    count = volume if volume is not None else policy.get("launchVolume" if mode == "launch" else "growthVolume")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("Explicit configurable non-negative batch volume is required")
    existing = set(data.get("existingIntentKeys", []))
    candidates = []
    for query in data.get("queries", []):
        if not query.get("primaryKeyword") or not query.get("intentKey") or not query.get("queryEvidence"):
            raise ValueError("Query candidates need primaryKeyword, intentKey and actual queryEvidence")
        if query.get("queryClass") not in PRIORITY or query.get("pageType") not in blueprint["pageTypes"]:
            raise ValueError("Query class/page type is not allowed by the Blueprint")
        if query["intentKey"] not in existing:
            candidates.append(query)
    # Same CTA/information requirement belongs to one intent. Highest-priority
    # primary keyword wins; synonyms remain evidence, not duplicate pages.
    candidates.sort(key=lambda q: (PRIORITY[q["queryClass"]], -q.get("queryPriority", 0), q["primaryKeyword"]))
    grouped = {}
    for query in candidates:
        intent = query["intentKey"]
        if intent not in grouped:
            grouped[intent] = {**query, "keywordCluster": list(query.get("keywordCluster", [query["primaryKeyword"]]))}
        else:
            grouped[intent]["keywordCluster"] = list(dict.fromkeys(grouped[intent]["keywordCluster"] + [query["primaryKeyword"]]))
    selected = list(grouped.values())[:count]
    checks = [fact.get("key") for fact in fingerprint.get("facts", []) if fact.get("sourceLevel") in {"industry_default", "unknown"}]
    return {"state": "planned", "mode": mode, "volume": count, "availableIntents": len(grouped), "selected": selected, "humanCheckRequired": checks, "schedulesChanged": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=["launch", "growth"], required=True)
    parser.add_argument("--volume", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try: result = plan(json.loads(args.input.read_text()), args.mode, args.volume)
    except (ValueError, KeyError) as error: raise SystemExit(f"PLAN VALIDATION FAILED: {error}")
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output: args.output.write_text(text)
    else: print(text, end="")
