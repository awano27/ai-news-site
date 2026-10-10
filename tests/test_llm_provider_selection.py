"""PowerShell provider selection for the local daily override."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'run_daily_override.ps1'


def _pwsh():
    for candidate in (os.environ.get('PWSH'), '/tmp/pwsh/pwsh', shutil.which('pwsh')):
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


def select(key, confirmed):
    pwsh = _pwsh()
    if pwsh is None:
        pytest.skip('pwsh is not available')
    command = (
        f". '{SCRIPT}' -DefineFunctionsOnly; "
        "$result = Select-DailyLlmProvider -ApiKey $env:SEL_KEY -Confirmed $env:SEL_CONFIRMED; "
        "Write-Output ($result.Provider + '|' + $result.Reason)"
    )
    env = dict(os.environ)
    env['SEL_KEY'] = key
    env['SEL_CONFIRMED'] = confirmed
    result = subprocess.run(
        [str(pwsh), '-NoProfile', '-Command', command],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    provider, reason = result.stdout.strip().split('|', 1)
    if key:
        assert key not in provider
        assert key not in reason
    return provider, reason


def test_nvidia_requires_nvapi_prefix_and_exact_confirmation():
    assert select('nvapi-super-secret', 'true') == ('nvidia', '')
    assert select('NVAPI-super-secret', 'true') == ('nvidia', '')
    provider, reason = select('nvapi-super-secret', '')
    assert provider == 'ollama'
    assert reason == "NVIDIA key found but NVIDIA_PRODUCTION_USE_CONFIRMED is not 'true'; using ollama."
    provider, reason = select('nvapi-super-secret', 'True')
    assert provider == 'ollama'
    assert 'true' in reason
    assert select('', 'true') == ('ollama', '')
    assert select('sk-super-secret', 'true') == ('ollama', '')


def test_runner_logs_the_reason_without_embedding_the_key():
    text = SCRIPT.read_text(encoding='utf-8')
    assert 'Select-DailyLlmProvider' in text
    assert 'NVIDIA_PRODUCTION_USE_CONFIRMED' in text
    assert 'nvapi-' in text
    assert 'Write-RunnerLog $env:NVIDIA_API_KEY' not in text
    assert 'Write-RunnerLog "$env:NVIDIA_API_KEY' not in text
