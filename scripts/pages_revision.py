#!/usr/bin/env python3
"""Record/resolve public build identity without credentials or content generation."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

FILENAME = 'publication-revision.json'


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'schema_version', 'revision', 'workflow_run_id', 'daily_date'}:
        raise ValueError('invalid public build identity fields')
    if type(payload['schema_version']) is not int or payload['schema_version'] != 1 or not re.fullmatch(r'[0-9a-f]{40}', str(payload['revision'])):
        raise ValueError('invalid public build revision')
    if type(payload['workflow_run_id']) is not int or payload['workflow_run_id'] <= 0:
        raise ValueError('invalid public workflow run')
    if date.fromisoformat(payload['daily_date']).isoformat() != payload['daily_date']:
        raise ValueError('invalid public edition date')
    return payload


def record(root, site, revision, run_id):
    root, site = Path(root).resolve(), Path(site).resolve()
    if site == root or root in site.parents or not site.is_dir():
        raise ValueError('build identity belongs only in the separate staged artifact')
    daily = json.loads((root/'daily-news/data.json').read_text(encoding='utf8'))
    payload = validate(dict(schema_version=1, revision=revision, workflow_run_id=run_id, daily_date=daily['date']))
    (site/FILENAME).write_text(json.dumps(payload, sort_keys=True)+'\n', encoding='utf8')
    return payload


def resolve(base_url):
    request=urllib.request.Request(base_url.rstrip('/')+'/'+FILENAME,
                                  headers={'Cache-Control':'no-cache', 'User-Agent':'VisionHub-build-identity/1'})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw=response.read(8193)
    if len(raw)>8192:
        raise ValueError('oversized public build identity')
    return validate(json.loads(raw))


def matches(payload, revision=None, run_id=None):
    validate(payload)
    if revision is not None and payload['revision'] != revision:
        raise ValueError('published revision differs from actual Pages build')
    if run_id is not None and payload['workflow_run_id'] != run_id:
        raise ValueError('published workflow run differs from actual Pages build')
    return payload


def verify_stable_publication(base_url, verifier, *, reader=resolve, attempts=3):
    for _ in range(attempts):
        before=validate(reader(base_url))
        passed=verifier(before)
        after=validate(reader(base_url))
        if before!=after:
            print('Public deployment changed during verification; reselecting actual revision.')
            continue
        if not passed:
            raise ValueError('strict public verification failed for a stable revision')
        return after
    raise ValueError('public deployment changed during all attempts; no verification claimed')


def verify_revision(root, base_url, payload):
    root=Path(root).resolve()
    def run(command, cwd=root):
        result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,timeout=180)
        if result.stdout:print(result.stdout,end='')
        if result.stderr:print(result.stderr,end='',file=sys.stderr)
        return result.returncode==0
    if not run(['git','fetch','origin','main']):return False
    if not run(['git','merge-base','--is-ancestor',payload['revision'],'origin/main']):return False
    # Use an isolated disposable clone: compilation must not alter the guard's
    # original checkout or block switching revisions after a concurrent deploy.
    with tempfile.TemporaryDirectory(prefix='visionhub-public-guard-') as temporary:
        checkout=Path(temporary)/'checkout'
        if not run(['git','clone','--shared','--no-checkout',str(root),str(checkout)]):return False
        if not run(['git','checkout','--detach',payload['revision']],checkout):return False
        commands=[
            ['node','scripts/build-homepage-latest.js','--strict'],
            [sys.executable,'scripts/check_homepage_sync.py','--base-url',base_url,'--attempts','1'],
            [sys.executable,'scripts/check_daily_publication.py','--root',str(checkout),'--base-url',base_url,
             '--date',payload['daily_date'],'--require-quality','--check-urls','--attempts','1'],
        ]
        return all(run(command,checkout) for command in commands)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    write=sub.add_parser('record')
    write.add_argument('--root',type=Path,default=Path('.'))
    write.add_argument('--site',type=Path,required=True)
    write.add_argument('--revision',required=True)
    write.add_argument('--run-id',type=int,required=True)
    read=sub.add_parser('resolve')
    read.add_argument('--base-url',default='https://visionhub.jp')
    read.add_argument('--github-output',type=Path)
    read.add_argument('--expect-revision')
    read.add_argument('--expect-run-id',type=int)
    check=sub.add_parser('verify-public')
    check.add_argument('--root',type=Path,default=Path('.'))
    check.add_argument('--base-url',default='https://visionhub.jp')
    args=parser.parse_args(argv)
    try:
        if args.command=='verify-public':
            payload=verify_stable_publication(args.base_url,lambda value:verify_revision(args.root,args.base_url,value))
            print('PASS: stable published revision, TOP and strict daily content verified')
        else:
            payload=record(args.root,args.site,args.revision,args.run_id) if args.command=='record' else resolve(args.base_url)
        if args.command=='resolve':
            matches(payload,args.expect_revision,args.expect_run_id)
        if args.command=='resolve' and args.github_output:
            with args.github_output.open('a',encoding='utf8') as output:
                output.write('revision='+payload['revision']+'\n')
        print(json.dumps(payload,sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print('Build identity unavailable or invalid: '+type(error).__name__)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
