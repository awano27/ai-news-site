"""Compare supplemental failures with HEAD in an isolated read-only copy."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='visionhub-head-baseline-') as raw:
    target = Path(raw)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], cwd=ROOT).decode('utf-8').splitlines()
    latest = max(name for name in names if name.startswith('presentations/day_slides/day_slide_') and name.endswith('.html'))
    selected = [name for name in names if name == 'index.html' or name == latest or name.startswith('scripts/') and (name.endswith('.py') or name.endswith('.js'))]
    for name in selected:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT))
    test_names = ['tests/test_day_slides_latest_contract.py', 'tests/test_ux_improvements.py']
    for name in test_names:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    result = subprocess.run([sys.executable, '-m', 'pytest', *test_names, '-q'], cwd=target, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / 'supplemental-head-baseline.log').write_bytes(result.stdout)
    print(result.stdout.decode('utf-8', errors='replace')[-6500:])
    print('baseline_exit_code=' + str(result.returncode))
