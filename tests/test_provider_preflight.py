import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.auto_collect.provider_preflight import inspect_provider

ROOT = Path(__file__).resolve().parents[1]


def configured():
    return {"NVIDIA_API_KEY": "nvapi-test-secret", "NVIDIA_MODEL": "test-model",
            "NVIDIA_PRODUCTION_USE_CONFIRMED": "true"}


def test_all_missing_configuration_is_reported_without_any_api_call():
    def forbidden(name):
        pytest.fail("Unverified provider must not be contacted")
    result = inspect_provider("nvidia", {}, probe=True, factory=forbidden)
    assert result["missing_settings"] == ["NVIDIA_MODEL", "NVIDIA_API_KEY", "NVIDIA_PRODUCTION_USE_CONFIRMED"]
    assert result["failure_reason"] == "model_not_configured"
    assert result["status"] == "blocked" and result["probe_performed"] is False


@pytest.mark.parametrize("flag", ["false", "True", "", "yes"])
def test_confirmation_cannot_be_inferred_or_changed(flag):
    env = configured()
    env["NVIDIA_PRODUCTION_USE_CONFIRMED"] = flag
    before = dict(env)
    result = inspect_provider("nvidia", env, probe=True, factory=lambda _: pytest.fail("No call"))
    assert result["failure_reason"] == "production_entitlement_unverified"
    assert env == before
    assert "nvapi-test-secret" not in json.dumps(result)


def test_configuration_only_never_claims_provider_or_publication_ready():
    result = inspect_provider("nvidia", configured(), factory=lambda _: pytest.fail("No call"))
    assert result["status"] == "configured"
    assert not result["probe_performed"] and not result["publication_verified"]


def test_local_ready_is_only_a_health_result():
    calls = []
    def factory(name):
        calls.append(name)
        return SimpleNamespace(available=True, last_error="")
    result = inspect_provider("ollama", {}, probe=True, factory=factory)
    assert calls == ["ollama"] and result["status"] == "ready"
    assert not result["publication_verified"]


def test_probe_errors_do_not_expose_response_or_credentials():
    result = inspect_provider("nvidia", configured(), probe=True,
                              factory=lambda _: SimpleNamespace(available=False, last_error="nvapi-test-secret"))
    assert result["failure_reason"] == "provider_unavailable"
    assert "nvapi-test-secret" not in json.dumps(result)


def test_cli_failure_saves_diagnosis_and_preserves_existing_publication(tmp_path):
    public = tmp_path / "index.html"
    public.write_bytes(b"last verified edition")
    env = {**os.environ, "NVIDIA_API_KEY": "nvapi-test-secret", "NVIDIA_MODEL": "",
           "NVIDIA_PRODUCTION_USE_CONFIRMED": "false"}
    output = tmp_path / "logs/provider_preflight.json"
    result = subprocess.run([sys.executable, "-m", "src.auto_collect.provider_preflight", "--provider", "nvidia",
                             "--probe", "--output", str(output)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 1
    assert public.read_bytes() == b"last verified edition"
    assert json.loads(output.read_text())["probe_performed"] is False
    assert "nvapi-test-secret" not in result.stdout + result.stderr + output.read_text()


def test_override_cli_uses_existing_ollama_when_confirmed_key_has_no_model():
    env = {**os.environ, "NVIDIA_API_KEY": "nvapi-test-secret", "NVIDIA_MODEL": "",
           "NVIDIA_PRODUCTION_USE_CONFIRMED": "true"}
    result = subprocess.run([sys.executable, "-m", "src.auto_collect.provider_selection"], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0 and "provider=ollama" in result.stdout
    assert "NVIDIA_MODEL is missing" in result.stdout
    assert "nvapi-test-secret" not in result.stdout + result.stderr


def test_preflight_runs_before_collection_and_failure_artifact_keeps_its_report():
    workflow = (ROOT / ".github/workflows/auto-daily-report-cloud-fallback.yml").read_text(encoding="utf-8")
    assert workflow.index("provider_preflight --provider nvidia --probe") < workflow.index("src.auto_collect.main --provider nvidia")
    assert "logs/auto_collect/provider_preflight.json" in workflow.split("Retain failure diagnostics")[1]
    runner = (ROOT / "scripts/run_daily_override.ps1").read_text(encoding="utf-8")
    assert runner.index('"src.auto_collect.provider_preflight"') < runner.index('"src.auto_collect.main"')
    assert "--require-quality" in runner
