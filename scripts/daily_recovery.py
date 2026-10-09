#!/usr/bin/env python3
"""Bounded, audited Actions recovery. Upload a reservation artifact before POST.

The serialized watchdog owns the per-kind ledger. Reservations count even if a
POST fails or the run is not visible, so rejection cannot cause endless retries.
Only GitHub-hosted metadata and non-secret configuration are inspected.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

JST = timezone(timedelta(hours=9))
ACTIVE = {'queued', 'in_progress', 'waiting', 'pending', 'requested'}
WORKFLOWS = {'primary': 'auto-daily-report-cloud-fallback.yml', 'pages': 'pages.yml'}
MAX_ATTEMPTS = 2
COOLDOWN_SECONDS = 30 * 60
TRANSIENT_REASONS = {"network_error", "http_429", "http_500", "http_502", "http_503", "http_504", "collection_unavailable", "transient_generation_failed"}


class RecoveryError(RuntimeError):
    pass


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def ledger_prefix(kind, now):
    return f'daily-recovery-{kind}-{now.astimezone(JST).date().isoformat()}-'


def plan_recovery(runs, artifacts, kind, now):
    if any(run.get('status') in ACTIVE for run in runs):
        return {'dispatch': False, 'reason': 'target workflow is queued or in progress'}
    reservations = [item for item in artifacts if item.get('name', '').startswith(ledger_prefix(kind, now))]
    if len(reservations) >= MAX_ATTEMPTS:
        raise RecoveryError(f'{kind} recovery budget exhausted: {MAX_ATTEMPTS} reservations for this JST day; inspect failed runs and provider configuration')
    if any((now - instant(item['created_at'])).total_seconds() < COOLDOWN_SECONDS for item in reservations):
        return {'dispatch': False, 'reason': 'recovery cooldown has not elapsed'}
    return {'dispatch': True, 'reason': 'content verification failed and bounded recovery is available'}


def gh(*args):
    result = subprocess.run(['gh', 'api', *args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        # gh errors can include account or response detail; do not echo raw output.
        raise RecoveryError(f'GitHub API request failed (gh exit {result.returncode}); inspect Actions permissions or service availability')
    if '--include' in args:
        return result.stdout
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RecoveryError('GitHub API returned invalid JSON') from error


def list_runs(repo, workflow):
    pages = gh(f'repos/{repo}/actions/workflows/{workflow}/runs?branch=main&per_page=100', '--paginate', '--slurp')
    return [run for page in pages for run in page.get('workflow_runs', [])]


def list_artifacts(repo):
    pages = gh(f'repos/{repo}/actions/artifacts?per_page=100', '--paginate', '--slurp')
    return [artifact for page in pages for artifact in page.get('artifacts', [])]


def dispatch_workflow(repo, workflow, now, prior_runs):
    response = gh(f'repos/{repo}/actions/workflows/{workflow}/dispatches', '--method', 'POST', '--include', '-f', 'ref=main')
    if not re.search(r'^HTTP/\S+ 204\b', response, flags=re.M):
        raise RecoveryError('workflow_dispatch was not acknowledged with HTTP 204; reservation retained, no automatic repeat POST')
    previous_ids = {run.get('id') for run in prior_runs}
    for attempt in range(6):
        if attempt:
            time.sleep(5)
        for run in list_runs(repo, workflow):
            if run.get('id') not in previous_ids and run.get('event') == 'workflow_dispatch' and instant(run['created_at']) >= now - timedelta(seconds=5):
                return {'run_id': run['id'], 'url': run.get('html_url'), 'reason': 'dispatch acknowledged and workflow run visible; publication remains pending'}
    raise RecoveryError('workflow_dispatch acknowledged but run not visible after six checks; reservation retained, no repeat POST')


def primary_retry_eligible(latest, diagnostic):
    if latest is None or latest.get('conclusion') in {'success', 'timed_out'}:
        return True
    reason = (diagnostic or {}).get('failure_reason', 'missing diagnostic')
    if latest.get('conclusion') == 'failure' and reason in TRANSIENT_REASONS:
        return True
    raise RecoveryError(f'latest primary failure is not retryable ({reason}); inspect diagnostics and fix configuration/quality first')


def primary_diagnostic(repo, run):
    if run.get('conclusion') != 'failure':
        return None
    run_id = str(run['id'])
    attempt = str(run.get('run_attempt', 1))
    with tempfile.TemporaryDirectory(prefix='daily-recovery-') as directory:
        result = subprocess.run(['gh', 'run', 'download', run_id, '--repo', repo,
                                 '--name', f'daily-quality-{run_id}-{attempt}', '--dir', directory],
                                capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RecoveryError('primary failure diagnostics could not be downloaded; no unclassified retry')
        paths = sorted(Path(directory).rglob('daily_quality_*.json'))
        if len(paths) != 1:
            raise RecoveryError('primary failure diagnostics are missing or ambiguous; no unclassified retry')
        data = json.loads(paths[0].read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise RecoveryError('primary failure diagnostic is invalid')
        return data


def emit(values):
    print(json.dumps(values, ensure_ascii=False))
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as stream:
            for key, value in values.items():
                stream.write(f'{key}={str(value).lower() if isinstance(value, bool) else value}\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', required=True, choices=WORKFLOWS)
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--plan', action='store_true')
    modes.add_argument('--dispatch', action='store_true')
    parser.add_argument('--reservation', type=Path, default=Path('daily-recovery-state/reservation.json'))
    args = parser.parse_args(argv)
    try:
        if not args.repo or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
            raise RecoveryError('valid repository owner/name is required')
        now = datetime.now(timezone.utc)
        if args.kind == 'primary':
            if not os.environ.get('NVIDIA_MODEL', '').strip():
                raise RecoveryError('permanent configuration blocker: NVIDIA_MODEL is not configured; no recovery dispatch')
            if os.environ.get('NVIDIA_PRODUCTION_USE_CONFIRMED') != 'true':
                raise RecoveryError('permanent configuration blocker: NVIDIA production entitlement is unverified; no recovery dispatch')
        workflow = WORKFLOWS[args.kind]
        runs = list_runs(args.repo, workflow)
        artifacts = list_artifacts(args.repo)
        if args.plan:
            plan = plan_recovery(runs, artifacts, args.kind, now)
            if plan['dispatch'] and args.kind == 'primary':
                latest = max(runs, key=lambda run: run.get('created_at', ''), default=None)
                primary_retry_eligible(latest, primary_diagnostic(args.repo, latest) if latest else None)
            if plan['dispatch']:
                run_id = os.environ.get('GITHUB_RUN_ID')
                attempt = os.environ.get('GITHUB_RUN_ATTEMPT')
                if not run_id or not attempt or not run_id.isdigit() or not attempt.isdigit():
                    raise RecoveryError('Actions run ID and attempt are required for a unique reservation')
                name = ledger_prefix(args.kind, now) + f'{run_id}-{attempt}'
                args.reservation.parent.mkdir(parents=True, exist_ok=True)
                args.reservation.write_text(json.dumps({'name': name, 'kind': args.kind, 'created_at': now.isoformat()}), encoding='utf-8')
                plan['reservation_name'] = name
            emit(plan)
        else:
            reservation = json.loads(args.reservation.read_text(encoding='utf-8'))
            name = reservation.get('name', '')
            if reservation.get('kind') != args.kind or not name.startswith(ledger_prefix(args.kind, now)):
                raise RecoveryError('recovery reservation does not match kind/current JST day')
            if not any(item.get('name') == name for item in artifacts):
                raise RecoveryError('reservation artifact is not visible; no dispatch without durable retry accounting')
            others = [item for item in artifacts if item.get('name') != name]
            plan = plan_recovery(runs, others, args.kind, now)
            if not plan['dispatch']:
                emit(plan)
                return 0
            if args.kind == 'primary':
                latest = max(runs, key=lambda run: run.get('created_at', ''), default=None)
                primary_retry_eligible(latest, primary_diagnostic(args.repo, latest) if latest else None)
            emit(dispatch_workflow(args.repo, workflow, now, runs))
        return 0
    except (RecoveryError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'::error::{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
