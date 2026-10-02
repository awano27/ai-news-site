"""Read-only final evidence and change inventory."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8')

baseline = json.loads((OUT / 'baseline-dirty-sha256.json').read_text(encoding='utf-8-sig'))
checks = [{'path': item['path'], 'unchanged': hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest().upper() == item['sha256']} for item in baseline]
for name in ['daily-news/index.html', 'daily-news/news_detail.html']:
    checks.append({'path': name, 'unchanged_from_HEAD': (ROOT / name).read_bytes() == subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)})
checks.append({'HEAD': git('rev-parse', 'HEAD').strip(), 'staged_paths': git('diff', '--cached', '--name-only').splitlines()})
(OUT / 'preservation.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
existing = {item['path'] for item in baseline}
tracked = [name for name in git('diff', '--name-only').splitlines() if name not in existing]
pending = ['.github/workflows/publish-generated-content.yml', 'requirements-ingest.txt', 'sources.yaml', 'script/pages_heal.py', 'scripts/config.py', 'scripts/ingest.py', 'scripts/validate.py', 'scripts/collectors/producthunt.py', 'scripts/collectors/github.py', 'scripts/public_html.py', 'src/auto_collect/output_validation.py', 'src/generators/detail_analysis_generator.py', 'tests/test_distribution_workflows.py', 'tests/test_render_safety.py', 'tests/test_site_freshness.py', 'tests/test_analytics_contract.py', 'tests/test_article_contract.py', 'tests/test_publish_image2_day_slide.py', 'tests/verify_analytics_events.cjs']
for name in pending:
    assert (ROOT / name).is_file(), name
    assert subprocess.run(['git', 'check-ignore', '-q', name], cwd=ROOT).returncode == 1, name
(OUT / 'CHANGE-FILES.md').write_text('# 今回の変更一覧\n\n既存dirtyのCLAUDE.mdとSKILL.mdは除外。stage/commitなし。\n\n## 追跡済みファイルの修正\n\n' + '\n'.join('- `' + name + '`' for name in tracked) + '\n\n## 追加・配布予定のコードと依存設定\n\n' + '\n'.join('- `' + name + '`' for name in pending) + '\n\n作業記録・fixture・ログ・スクリーンショット: `docs/plans/2026-10-03-codebase-improvement/`。新規配布予定には以前から存在したignore済みの非秘密ファイルも含む。\n', encoding='utf-8')
commands = [('coding-guide', ['scripts/check_coding_guide_integrity.py']), ('claim-evidence', ['scripts/check_claim_evidence.py']), ('analytics-config', ['scripts/check_analytics_config.py']), ('analytics-coverage', ['scripts/check_analytics_coverage.py'])]
results = {}
for name, args in commands:
    result = subprocess.run([sys.executable, *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / (name + '.log')).write_bytes(result.stdout)
    results[name] = {'exit_code': result.returncode, 'output': result.stdout.decode('utf-8', errors='replace')}
(OUT / 'static-checks.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'preservation': checks, 'tracked_changed': len(tracked), 'pending_code': len(pending), 'checks': results}, ensure_ascii=False))
