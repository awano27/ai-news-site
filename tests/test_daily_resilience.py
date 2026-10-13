import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml
from scripts import pages_revision

ROOT = Path(__file__).resolve().parents[1]


def test_configuration_preflight_needs_only_standard_library():
    env = {'NVIDIA_MODEL': '', 'NVIDIA_API_KEY': '', 'NVIDIA_PRODUCTION_USE_CONFIRMED': ''}
    import os
    result = subprocess.run([sys.executable, '-S', '-m', 'src.auto_collect.provider_preflight', '--provider', 'nvidia'],
                            cwd=ROOT, env={**os.environ, **env, 'PYTHONPATH': str(ROOT)}, capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)['status'] == 'blocked'
    assert 'ModuleNotFoundError' not in result.stderr


def test_cloud_configuration_checked_before_dependency_install():
    text = (ROOT/'.github/workflows/auto-daily-report-cloud-fallback.yml').read_text(encoding='utf8')
    assert text.index('Diagnose configuration before installing dependencies') < text.index('Install deps')
    assert "53 20 * * *" in text


def test_live_guard_runs_after_pages_and_uses_published_revision():
    data = yaml.safe_load((ROOT/'.github/workflows/freshness-guard.yml').read_text(encoding='utf8'))
    trigger = data.get('on', data.get(True))
    assert trigger['workflow_run']['workflows'] == ['Deploy to GitHub Pages']
    jobs=data['jobs']
    assert 'check_homepage_sync.py --base-url' not in str(jobs['check'])
    assert 'success' in jobs['published']['if']
    text=str(jobs['published'])
    assert 'pages_revision.py verify-public' in text
    verifier=(ROOT/'scripts/pages_revision.py').read_text(encoding='utf8')
    assert "'merge-base','--is-ancestor'" in verifier
    assert '--require-quality' in verifier


def test_pages_records_actual_build_not_event_revision():
    data=yaml.safe_load((ROOT/'.github/workflows/pages.yml').read_text(encoding='utf8'))
    text=str(data['jobs']['build'])
    assert 'pages_revision.py record' in text
    assert 'steps.revision.outputs.sha' in text
    assert 'github.run_id' in text


def identity(**changes):
    value=dict(schema_version=1,revision='a'*40,workflow_run_id=123,daily_date='2026-10-13')
    value.update(changes)
    return value


@pytest.mark.parametrize('changes', [dict(schema_version=True),dict(revision='main'),dict(revision='a'*40+'\nunsafe=1'),
                                    dict(workflow_run_id=True),dict(workflow_run_id=0),dict(daily_date='2026-02-30'),
                                    dict(daily_date='20261013'),dict(api_key='never-public')])
def test_invalid_identity_is_rejected(changes):
    with pytest.raises((ValueError,TypeError)):
        pages_revision.validate(identity(**changes))


def test_record_uses_actual_existing_edition_and_whitelisted_fields(tmp_path):
    root=tmp_path/'repo';site=tmp_path/'staged';site.mkdir()
    (root/'daily-news').mkdir(parents=True)
    (root/'daily-news/data.json').write_text(json.dumps({'date':'2026-10-12','private':'not copied'}))
    payload=pages_revision.record(root,site,'a'*40,123)
    assert payload['daily_date']=='2026-10-12'
    assert json.loads((site/pages_revision.FILENAME).read_text())==payload
    assert 'private' not in json.dumps(payload)
    with pytest.raises(ValueError):pages_revision.record(root,root,'a'*40,123)
    assert not (root/pages_revision.FILENAME).exists()


def test_missing_identity_does_not_export_a_guessed_revision(tmp_path,monkeypatch):
    def unavailable(_):raise OSError('not deployed')
    monkeypatch.setattr(pages_revision,'resolve',unavailable)
    output=tmp_path/'github-output'
    assert pages_revision.main(['resolve','--github-output',str(output)])==1
    assert not output.exists()


def test_parallel_publications_follow_public_sha_not_newer_main(tmp_path):
    import functools,http.server,threading
    repo=tmp_path/'repo';repo.mkdir();site=tmp_path/'public';site.mkdir()
    def git(*args):
        result=subprocess.run(['git',*args],cwd=repo,capture_output=True,text=True,check=True)
        return result.stdout.strip()
    git('init','-b','main');git('config','user.email','test@example.invalid');git('config','user.name','Test')
    (repo/'daily-news').mkdir()
    (repo/'daily-news/data.json').write_text(json.dumps({'date':'2026-10-13'}))
    (repo/'index.html').write_text('published build A')
    git('add','.');git('commit','-m','A');sha_a=git('rev-parse','HEAD')
    (repo/'index.html').write_text('newer build B')
    git('add','.');git('commit','-m','B');sha_b=git('rev-parse','HEAD')
    git('update-ref','refs/remotes/origin/main',sha_b)
    pages_revision.record(repo,site,sha_a,101)
    (site/'index.html').write_text('published build A')
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(site))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        url=f'http://127.0.0.1:{server.server_port}'
        resolved=pages_revision.resolve(url)
        assert resolved['revision']==sha_a and resolved['revision']!=sha_b
        git('merge-base','--is-ancestor',resolved['revision'],'origin/main')
        git('checkout','--detach',resolved['revision'])
        assert (repo/'index.html').read_text()==(site/'index.html').read_text()
        # A later event may arrive after B is already public. Follow B, not the
        # older event's SHA, and still verify it belongs to approved main history.
        pages_revision.record(repo,site,sha_b,102)
        (site/'index.html').write_text('newer build B')
        resolved=pages_revision.resolve(url)
        assert resolved['revision']==sha_b and resolved['workflow_run_id']==102
        git('merge-base','--is-ancestor',resolved['revision'],'origin/main')
        git('checkout','--detach',resolved['revision'])
        assert (repo/'index.html').read_text()==(site/'index.html').read_text()
    finally:
        server.shutdown();server.server_close();thread.join()


def test_resolver_rejects_oversized_identity(monkeypatch):
    from io import BytesIO
    monkeypatch.setattr(pages_revision.urllib.request,'urlopen',lambda *a,**k:BytesIO(b'x'*8193))
    with pytest.raises(ValueError,match='oversized'):pages_revision.resolve('https://visionhub.jp')


def test_quality_requirements_are_not_changed_by_resilience_patch():
    from src.auto_collect.quality import MAX_EXCLUDED_RATIO
    assert MAX_EXCLUDED_RATIO==0.20
    text=(ROOT/'.github/workflows/auto-daily-report-cloud-fallback.yml').read_text(encoding='utf8')
    assert text.count('--require-quality')>=2
    assert "NVIDIA_PRODUCTION_USE_CONFIRMED: ${{ vars.NVIDIA_PRODUCTION_USE_CONFIRMED }}" in text
    assert 'NVIDIA_PRODUCTION_USE_CONFIRMED: true' not in text


@pytest.mark.parametrize('revision,run_id', [('b'*40,123),('a'*40,456)])
def test_pages_verify_rejects_different_artifact_even_if_date_matches(revision,run_id):
    with pytest.raises(ValueError):pages_revision.matches(identity(),revision,run_id)


def test_pages_verify_and_guard_accept_the_same_actual_identity():
    payload=identity()
    assert pages_revision.matches(payload,'a'*40,123)==payload
    assert pages_revision.matches(payload)==payload
    data=yaml.safe_load((ROOT/'.github/workflows/pages.yml').read_text(encoding='utf8'))
    assert 'needs.build.outputs.revision' in str(data['jobs']['verify'])
    assert '--expect-run-id' in str(data['jobs']['verify'])


def test_wake_option_is_only_a_plan_and_keeps_interactive_permissions(tmp_path):
    if sys.platform!='win32':pytest.skip('Windows native PlanOnly check')
    checkout=tmp_path/'never-created'
    result=subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'scripts/register_daily_override_task.ps1'),
                           '-CheckoutPath',str(checkout),'-WakeToRun','-PlanOnly'],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    plan=json.loads(result.stdout)
    assert plan['settings']['wakeToRun'] is True
    assert plan['settings']['startWhenAvailable'] is True
    assert plan['principal']=={'logonType':'InteractiveToken'}
    assert not checkout.exists()


def test_deployment_change_during_verification_reselects_new_public_revision():
    old=identity();new=identity(revision='b'*40,workflow_run_id=456)
    observations=iter([old,new,new,new]);verified=[]
    def verify(payload):
        verified.append(payload['revision'])
        return payload['revision']=='b'*40
    result=pages_revision.verify_stable_publication('https://visionhub.jp',verify,reader=lambda _:next(observations))
    assert result==new and verified==['a'*40,'b'*40]


def test_stable_invalid_content_is_a_failure_not_a_retry_or_success():
    calls=[]
    def verify(payload):calls.append(payload);return False
    with pytest.raises(ValueError,match='strict public verification failed'):
        pages_revision.verify_stable_publication('https://visionhub.jp',verify,reader=lambda _:identity())
    assert len(calls)==1


def test_continuous_deployment_changes_have_a_finite_failure_budget():
    observations=iter([identity(workflow_run_id=i) for i in range(1,7)])
    with pytest.raises(ValueError,match='changed during all attempts'):
        pages_revision.verify_stable_publication('https://visionhub.jp',lambda _:True,reader=lambda _:next(observations))
