from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 9, 22, 0, tzinfo=timezone.utc)  # October 10 JST


def workflow(name):
    return yaml.safe_load((ROOT / '.github/workflows' / name).read_text())


def events(data):
    return data.get('on', data.get(True, {}))


def recovery():
    script = ROOT / 'scripts/daily_recovery.py'
    assert script.exists(), 'Missing bounded recovery controller'
    spec = importlib.util.spec_from_file_location('daily_recovery', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('name', ['ai-news.yml', 'update-news.yml'])
def test_legacy_producers_are_manual_deprecation_not_scheduled_writers(name):
    data = workflow(name)
    assert 'schedule' not in events(data)
    assert 'workflow_dispatch' in events(data)
    assert data['permissions'].get('contents') == 'read'
    assert 'script/build_news.py' not in str(data['jobs'])
    assert 'deprecated' in str(data['jobs']).lower()


def test_cloud_daily_validates_quality_before_publish_and_keeps_diagnostics():
    data = workflow('auto-daily-report-cloud-fallback.yml')
    steps = data['jobs']['primary']['steps']
    runs = '\n'.join(s.get('run', '') for s in steps)
    assert runs.index('sync_daily_search.py') < runs.index('build-homepage-latest.js')
    assert runs.index('check_daily_publication.py') < runs.index('publish_daily_report.py')
    assert '--require-quality' in runs
    diagnostics = [s for s in steps if s.get('uses', '').startswith('actions/upload-artifact@')]
    assert any(s.get('if') == 'failure()' and 'logs/auto_collect/daily_quality_' in str(s.get('with')) for s in diagnostics)
    assert '|| true' not in runs


def test_pages_explicitly_follows_successful_cloud_run_on_current_main():
    data = workflow('pages.yml')
    triggers = events(data)
    assert triggers['workflow_run']['workflows'] == ['Auto Daily Report — Cloud Primary']
    assert triggers['workflow_run']['types'] == ['completed']
    assert 'success' in data['jobs']['build']['if']
    steps = data['jobs']['build']['steps']
    checkout = next(s for s in steps if s.get('uses', '').startswith('actions/checkout@'))
    assert checkout['with']['ref'] == 'main'
    runs = '\n'.join(s.get('run', '') for s in steps)
    assert runs.index('build_search_index.py') < runs.index('build-homepage-latest.js')
    assert 'check_daily_publication.py' in runs
    verify = data['jobs']['verify']
    assert 'deploy' in verify['needs']
    assert '--base-url' in str(verify)
    assert '--require-quality' in str(verify)
    assert 'git push' not in str(data)


@pytest.mark.parametrize(('name', 'mode'), [('auto-daily-report-safety.yml', 'primary'), ('pages-heal.yml', 'pages')])
def test_watchdogs_validate_content_reserve_attempt_then_dispatch(name, mode):
    data = workflow(name)
    assert data['permissions']['actions'] == 'write'
    assert data['permissions']['contents'] == 'read'
    assert data['concurrency']['cancel-in-progress'] is False
    text = str(data)
    assert 'check_daily_publication.py' in text
    assert f'--kind {mode}' in text
    assert '--plan' in text and '--dispatch' in text
    assert 'actions/upload-artifact@v4' in text
    assert '|| true' not in text
    assert '/pages/builds' not in text


def marker(number, minute=0, day='2026-10-10'):
    return {'name': f'daily-recovery-primary-{day}-{number}-1', 'created_at': f'2026-10-09T21:{minute:02d}:00Z', 'expired': False}


def test_recovery_skips_active_workflow_and_refuses_exhausted_jst_budget():
    module = recovery()
    assert module.plan_recovery([{'status': 'in_progress'}], [], 'primary', NOW)['dispatch'] is False
    with pytest.raises(module.RecoveryError, match='exhausted'):
        module.plan_recovery([], [marker(1), marker(2)], 'primary', NOW)


def test_recovery_counts_failed_attempt_reservations_and_observes_cooldown():
    module = recovery()
    assert module.plan_recovery([], [marker(1)], 'primary', NOW)['dispatch'] is True
    recent = marker(1)
    recent['created_at'] = '2026-10-09T21:55:00Z'
    result = module.plan_recovery([], [recent], 'primary', NOW)
    assert result['dispatch'] is False
    assert 'cooldown' in result['reason']
    # Yesterday's reservations cannot exhaust today's JST budget.
    assert module.plan_recovery([], [marker(1, day='2026-10-09'), marker(2, day='2026-10-09')], 'primary', NOW)['dispatch'] is True


def test_dispatch_checks_http_response_and_visible_run_without_ignoring_api_errors(monkeypatch):
    module = recovery()
    calls = []
    def gh(*args):
        calls.append(args)
        if '--method' in args:
            return 'HTTP/2.0 204 No Content\r\n\r\n'
        return [{'workflow_runs': [{'id': 42, 'event': 'workflow_dispatch', 'created_at': '2026-10-09T22:00:01Z', 'html_url': 'https://github.com/owner/repo/actions/runs/42'}]}]
    monkeypatch.setattr(module, 'gh', gh)
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    result = module.dispatch_workflow('owner/repo', 'pages.yml', NOW, [])
    assert result['run_id'] == 42
    assert '--include' in calls[0]
    assert any('ref=main' in value for value in calls[0])
    monkeypatch.setattr(module, 'gh', lambda *args: 'HTTP/2.0 403 Forbidden\r\n\r\n')
    with pytest.raises(module.RecoveryError, match='204'):
        module.dispatch_workflow('owner/repo', 'pages.yml', NOW, [])


def test_dispatch_visibility_wait_is_finite_and_does_not_repeat_post(monkeypatch):
    module = recovery()
    calls = []
    def gh(*args):
        calls.append(args)
        if '--method' in args:
            return 'HTTP/2.0 204 No Content\r\n\r\n'
        return [{'workflow_runs': []}]
    monkeypatch.setattr(module, 'gh', gh)
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    with pytest.raises(module.RecoveryError, match='not visible'):
        module.dispatch_workflow('owner/repo', 'pages.yml', NOW, [])
    assert sum('--method' in c for c in calls) == 1
    assert len(calls) <= 7


@pytest.mark.parametrize('reason', ['network_error', 'http_429', 'http_500', 'http_502', 'http_503', 'http_504', 'collection_unavailable', 'transient_generation_failed'])
def test_primary_retry_allows_only_classified_transient_failures(reason):
    module = recovery()
    assert module.primary_retry_eligible({'conclusion': 'failure'}, {'failure_reason': reason}) is True


@pytest.mark.parametrize('reason', ['model_not_configured', 'api_key_missing', 'production_entitlement_unverified', 'http_403', 'http_404', 'japanese_quality_failed', 'render_or_validation_failed', '', 'unknown'])
def test_primary_retry_blocks_permanent_or_unknown_failures(reason):
    module = recovery()
    with pytest.raises(module.RecoveryError, match='not retryable'):
        module.primary_retry_eligible({'conclusion': 'failure'}, {'failure_reason': reason})


def test_missing_schedule_and_timeout_are_retryable_but_cancelled_is_not():
    module = recovery()
    assert module.primary_retry_eligible(None, None)
    assert module.primary_retry_eligible({'conclusion': 'timed_out'}, None)
    with pytest.raises(module.RecoveryError, match='not retryable'):
        module.primary_retry_eligible({'conclusion': 'cancelled'}, None)


def test_offline_daily_ci_covers_push_and_pr_without_provider_secrets():
    path = ROOT / '.github/workflows/daily-pipeline-tests.yml'
    assert path.exists(), 'Missing offline daily regression workflow'
    data = workflow(path.name)
    assert 'push' in events(data) and 'pull_request' in events(data)
    assert 'schedule' not in events(data)
    text = str(data)
    for name in ['daily_quality', 'auto_collect_main', 'build_search_index', 'sync_daily_search', 'daily_publication', 'daily_workflows', 'publish_daily_report', 'finalize_daily_search', 'build_homepage_latest']:
        assert f'tests/test_{name}.py' in text
    assert 'secrets.' not in text
    assert 'daily_override_automation' not in text


def test_primary_missing_configuration_never_dispatches_or_reads_api(monkeypatch, capsys):
    module = recovery()
    monkeypatch.delenv('NVIDIA_MODEL', raising=False)
    monkeypatch.setattr(module, 'gh', lambda *args: pytest.fail('permanent config failure must not call GitHub'))
    assert module.main(['--kind', 'primary', '--repo', 'owner/repo', '--plan']) == 1
    assert 'configuration blocker' in capsys.readouterr().err


def test_dispatch_requires_uploaded_reservation(monkeypatch, tmp_path, capsys):
    module = recovery()
    reservation = tmp_path / 'reservation.json'
    import json
    now = datetime.now(timezone.utc)
    reservation.write_text(json.dumps({'name': module.ledger_prefix('pages', now) + '1-1', 'kind': 'pages'}))
    monkeypatch.setattr(module, 'list_runs', lambda *args: [])
    monkeypatch.setattr(module, 'list_artifacts', lambda *args: [])
    monkeypatch.setattr(module, 'dispatch_workflow', lambda *args: pytest.fail('must reserve first'))
    assert module.main(['--kind', 'pages', '--repo', 'owner/repo', '--dispatch', '--reservation', str(reservation)]) == 1
    assert 'no dispatch without durable' in capsys.readouterr().err


def test_primary_installs_lean_daily_dependencies():
    data = workflow('auto-daily-report-cloud-fallback.yml')
    steps = data['jobs']['primary']['steps']
    install = next(s['run'] for s in steps if s.get('name') == 'Install deps')
    assert 'pip install -r requirements-daily.txt' in install
    assert 'pip install -r requirements.txt' not in install
    assert 'pip install -e .' in install


def test_pages_packaging_does_not_hide_cleanup_errors():
    assert '|| true' not in str(workflow('pages.yml'))


def test_diagnostics_artifacts_match_the_actual_writer_log_directory():
    from src.auto_collect.config import LOG_DIR, PROJECT_ROOT
    paths = str(next(s for s in workflow('auto-daily-report-cloud-fallback.yml')['jobs']['primary']['steps'] if s.get('uses', '').startswith('actions/upload-artifact@'))['with']['path'])
    relative = LOG_DIR.relative_to(PROJECT_ROOT).as_posix()
    assert f'{relative}/daily_quality_*.json' in paths
    assert f'{relative}/daily_candidate_*.json' in paths
