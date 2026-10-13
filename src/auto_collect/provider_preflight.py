"""Diagnose an existing provider without generating or publishing news."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .llm_provider import make_provider


def inspect_provider(name, env, *, probe=False, factory=make_provider):
    missing = []
    reasons = []
    if name == "nvidia":
        for variable, reason in [("NVIDIA_MODEL", "model_not_configured"),
                                 ("NVIDIA_API_KEY", "api_key_missing")]:
            if not env.get(variable, "").strip():
                missing.append(variable)
                reasons.append(reason)
        if env.get("NVIDIA_PRODUCTION_USE_CONFIRMED") != "true":
            missing.append("NVIDIA_PRODUCTION_USE_CONFIRMED")
            reasons.append("production_entitlement_unverified")
    result = {"provider": name, "status": "blocked" if missing else "configured",
              "missing_settings": missing, "failure_reason": reasons[0] if reasons else None,
              "probe_performed": False, "publication_verified": False}
    if missing:
        result["recovery"] = ("Verify an applicable production entitlement and exact model yourself; "
                              "do not set confirmation merely to bypass this check. "
                              "Alternatively inspect the existing local Ollama override on the PC.")
        return result
    if probe:
        result["probe_performed"] = True
        try:
            provider = factory(name)
            result["status"] = "ready" if provider.available else "blocked"
            if not provider.available:
                # Never include endpoint responses, exception text, or credentials.
                reason = provider.last_error
                allowed = {"model_not_configured", "api_key_missing", "production_entitlement_unverified",
                           "network_error", "invalid_response", "retry_budget_exhausted"}
                result["failure_reason"] = reason if reason in allowed or reason in {
                    "http_400", "http_401", "http_403", "http_404", "http_429",
                    "http_500", "http_502", "http_503", "http_504"} else "provider_unavailable"
        except Exception:
            result["status"] = "blocked"
            result["failure_reason"] = "provider_probe_failed"
        result["recovery"] = ("Check the existing provider/service and retry the probe. "
                              "A ready probe does not certify article quality or publication.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=["nvidia", "ollama"])
    parser.add_argument("--probe", action="store_true", help="Send the existing provider a short OK health check")
    parser.add_argument("--output", type=Path, help="Save secret-free diagnostics outside public content")
    args = parser.parse_args(argv)
    result = inspect_provider(args.provider, os.environ, probe=args.probe)
    result["observed_at"] = datetime.now(timezone.utc).isoformat()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if result["status"] == "blocked" and os.environ.get("GITHUB_ACTIONS") == "true":
        print("::error::Provider preflight blocked: " + result["failure_reason"] +
              "; inspect provider_preflight.json. Previous publication is preserved.")
    return int(result["status"] == "blocked")


if __name__ == "__main__":
    raise SystemExit(main())
