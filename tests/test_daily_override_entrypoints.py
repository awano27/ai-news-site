from pathlib import Path
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def test_wsl_override_uses_strict_manifest_and_propagates_push_failure(tmp_path):
    tools=tmp_path/'bin';tools.mkdir()
    repo=tmp_path/'repo';repo.mkdir()
    calls=tmp_path/'calls.log'
    scripts={
        'curl':'#!/bin/bash\nexit 0\n',
        'git':'#!/bin/bash\nif [ "$1" = status ]; then echo " M index.html"; fi\nif [ "$1" = push ]; then exit 23; fi\nexit 0\n',
        'python3':'#!/bin/bash\necho "$*" >> "$CALLS_PATH"\nif [[ "$*" == *publish_daily_report.py* ]]; then exit 23; fi\nexit 0\n',
    }
    for name,text in scripts.items():
        path=tools/name;path.write_text(text);path.chmod(0o755)
    source=(ROOT/'src/auto_collect/run_daily.sh').read_text()
    runner=tmp_path/'run_daily.sh'
    runner.write_text(source.replace('PROJECT_DIR="/mnt/c/develop/ai-news-site"',f'PROJECT_DIR="{repo}"'))
    result=subprocess.run(['bash',str(runner),'daily'],env={**os.environ,'PATH':str(tools)+os.pathsep+os.environ['PATH'],'CALLS_PATH':str(calls)},capture_output=True,text=True)
    assert result.returncode==23
    commands=calls.read_text()
    assert 'publish_daily_report.py' in commands
    assert '--require-quality' in commands and '--push' in commands
    assert 'git add -A' not in source
