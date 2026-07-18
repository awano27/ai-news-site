# Auto Daily Report Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** NVIDIA NIM障害、PC停止、人間用dirty checkoutのいずれが発生しても、`auto_daily_report` を毎日生成・限定commit・公開できる二重化された自動更新経路を構築する。

**Architecture:** GitHub Actionsはprovider unavailable時に既存heuristic fallbackへ進み、共有manifestを使うPython publisherが公開成果物だけをcommit/pushする。Windowsの08:00 overrideは独立clone `C:\develop\ai-news-site-automation` で動き、PowerShell runnerがdirty退避・Git同期・pipeline・同じpublisherを順に実行する。人間用 `C:\develop\ai-news-site` は読み取り以外で触らない。

**Tech Stack:** Python 3.11、pytest、PowerShell 5.1、Windows Task Scheduler、Git/GitHub Actions、GitHub Pages、JSON manifest。

## Global Constraints

- 設計契約は `docs/superpowers/specs/2026-07-18-auto-daily-report-reliability-design.md`。
- 実装は `C:\develop\ai-news-site-fix-auto-daily-20260718` の `codex/fix-auto-daily-report-20260718` だけで行う。
- 人間用 `C:\develop\ai-news-site` の追跡済み変更103件・未追跡ファイル118件を変更、削除、stash、stage、commitしない。
- `git reset --hard`、`git clean`、force-pushを使用しない。
- 自動stageで `git add -u`、`git add -A`、ディレクトリ全体、広いglobを使用しない。
- provider unavailableはheuristic fallbackへ進む。headlineとGitHubがともに空の場合だけ出力前に失敗する。
- manifest外変更が1件でもあれば自動commit/pushしない。
- Windowsタスクは毎日08:00 JST、InteractiveToken、StartWhenAvailable、IgnoreNew、実行上限1時間を維持する。
- Cloud primaryは毎日06:00 JST相当の既存cronとworkflow_dispatchを維持する。
- API keyやsecret値をGit、テスト出力、ログへ書かない。
- TDDの各挙動はREDを確認してからproduction codeを変更する。
- `main` 反映後にActions、Pages、cache-busted live HTML/API、SHA-256一致まで確認する。

## File Map

- Modify: `src/auto_collect/main.py` — provider fallbackと真の空集合失敗。
- Create: `scripts/daily_report_paths.json` — 公開成果物の唯一のallowlist manifest。
- Create: `scripts/publish_daily_report.py` — manifest検証、限定stage、commit、push。
- Modify: `scripts/run_daily_override.bat` — repo相対の薄いlauncher。
- Create: `scripts/run_daily_override.ps1` — Windows runner。
- Create: `scripts/register_daily_override_task.ps1` — 独立cloneとTask Schedulerのidempotent installer。
- Modify: `.github/workflows/auto-daily-report-cloud-fallback.yml` — timeout/concurrency、共有publisher呼び出し。
- Modify: `.gitignore` — 上記scriptsと新規testsだけを明示的に追跡許可。
- Create: `tests/test_auto_collect_main.py` — provider/empty collection regression tests。
- Create: `tests/test_publish_daily_report.py` — manifest/publisher Git integration tests。
- Create: `tests/test_daily_override_automation.py` — launcher/runner/installer/workflow contract tests。
- Backfill: `input/day/0717.txt`、`daily-news/archive/2026-07-17.html`、`presentations/daily_reports/auto_daily_report_2026_07_17.html`、`public-pages/news/2026-07-17.json`。

## Dependencies and Parallel Work

- Task 1とTask 2のREDテスト作成は独立して並行可能。
- Task 3はTask 2のpublisher CLI契約に依存する。
- Task 4はTask 1とTask 2のproduction interfacesに依存する。
- Task 5のbackfillはコード実装と独立して検証できるが、commitは全テスト後に行う。
- Task 6のTask Scheduler切替は修正commitが `origin/main` に入った後でなければ実行しない。
- 最終統合、remote push、workflow dispatch、live verificationはSolが直接行う。

## Risks and Mitigations

- **Dirty primary checkout contamination:** 兄弟worktreeで実装し、backfillは4つの明示パスだけをコピーしてhash/dateを検証する。
- **Generated output drift:** publisherはGit statusとmanifestの差集合を拒否し、必要な新規出力はmanifest変更とテストを要求する。
- **Concurrent automation push:** publisherは通常push失敗後にfetch/rebaseして1回だけ再試行し、forceしない。
- **Interrupted local generation:** 次回起動時に独立clone内の全変更を日時付きstashへ保存し、stash IDをログへ残す。
- **Task installer points to wrong repo:** remote URLと `.git` を検証し、不一致なら削除せず失敗する。
- **Ollama/NVIDIA outage:** runnerは事前abortせず、Python側のprovider availabilityに応じてheuristic fallbackを使う。
- **Empty collection overwrites good page:** `main.py` はformatter/provider生成前に終了コード1とする。
- **Ignored governance files:** `.gitignore` に個別negationを追加し、`git check-ignore` と `git ls-files` で追跡を証明する。

---

### Task 1: Make provider outage fall back without allowing empty reports

**Files:**
- Create: `tests/test_auto_collect_main.py`
- Modify: `src/auto_collect/main.py:144-153`
- Modify: `.gitignore:168`

**Interfaces:**
- Consumes: `make_provider(name) -> LLMProvider` and `LLMProcessor(provider)`.
- Produces: `build_processor(provider_name: str) -> LLMProcessor`; `main()` exits 1 only when both headline and GitHub collections are empty.

- [ ] **Step 1: Allow only the new test file through `.gitignore`**

Re-open the ignored parent, keep its contents ignored by default, and allow only this new test:

```gitignore
!tests/
tests/*
!tests/test_auto_collect_main.py
```

- [ ] **Step 2: Write the unavailable-provider failing test**

Create a test that monkeypatches all collectors to deterministic in-memory collectors, makes `make_provider` return this real-behavior stub, and records the formatter input:

```python
class UnavailableProvider:
    name = "nvidia"
    available = False

    def chat(self, prompt: str):
        raise AssertionError("unavailable provider must not be called")


def test_unavailable_nvidia_uses_heuristic_fallback(monkeypatch, tmp_path):
    article = {
        "name": "New GPT model released",
        "tagline": "A deterministic fallback item",
        "links": {"official": "https://example.com/model"},
        "rss_source": "Example",
        "source_rank": 1,
    }
    captured = {}
    install_collectors(monkeypatch, articles=[article], github=[])
    monkeypatch.setattr(auto_main, "make_provider", lambda name: UnavailableProvider())
    monkeypatch.setattr(auto_main.DayFileFormatter, "write", lambda self, items, *a, **k: captured.setdefault("items", items))
    disable_renderers(monkeypatch)

    auto_main.main()

    assert captured["items"][0]["title"] == "New GPT model released"
    assert captured["items"][0]["score"] == 60
```

- [ ] **Step 3: Write the empty-collection failing test**

```python
def test_empty_headline_and_github_sources_exit_before_provider(monkeypatch):
    install_collectors(monkeypatch, articles=[], github=[])
    monkeypatch.setattr(auto_main, "make_provider", lambda name: pytest.fail("provider must not be built"))

    with pytest.raises(SystemExit) as exc:
        auto_main.main()

    assert exc.value.code == 1
```

- [ ] **Step 4: Run RED**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q tests/test_auto_collect_main.py
```

Expected: unavailable NVIDIA test fails with `SystemExit: 1`; empty-source test fails because current code returns normally.

- [ ] **Step 5: Implement the minimal fallback boundary**

Add:

```python
def build_processor(provider_name: str) -> LLMProcessor:
    provider = make_provider(provider_name)
    if not provider.available:
        logging.getLogger("auto_collect").warning(
            "[Main] %s provider unavailable; using deterministic heuristic fallback",
            provider_name,
        )
    return LLMProcessor(provider=provider)
```

Change the empty guard to `raise SystemExit(1)` and replace the NVIDIA-specific abort block with `processor = build_processor(args.provider)`.

- [ ] **Step 6: Run GREEN and regression tests**

Run:

```powershell
python -m pytest -q tests/test_auto_collect_main.py
python -m pytest -q
```

Expected: new tests pass and total suite has zero failures.

### Task 2: Enforce a manifest-only publication transaction

**Files:**
- Create: `scripts/daily_report_paths.json`
- Create: `scripts/publish_daily_report.py`
- Create: `tests/test_publish_daily_report.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `load_manifest(path: Path, report_date: date) -> PublicationManifest`.
- Produces: `validate_changes(repo: Path, manifest: PublicationManifest) -> list[str]`.
- CLI: `python scripts/publish_daily_report.py --repo PATH --date YYYY-MM-DD --message TEXT [--push]`.

- [ ] **Step 1: Add exact tracking exceptions**

Add only:

```gitignore
!scripts/daily_report_paths.json
!scripts/publish_daily_report.py
!tests/test_publish_daily_report.py
```

- [ ] **Step 2: Write manifest expansion tests**

Assert `2026-07-18` expands to `input/day/0718.txt`, `daily-news/archive/2026-07-18.html`, and `presentations/daily_reports/auto_daily_report_2026_07_18.html`; assert the OGP path is optional.

- [ ] **Step 3: Write a temporary-repository RED integration test**

Initialize a temporary Git repo with all required manifest files, commit baseline, modify one allowed file and one `unrelated.txt`, then run the publisher without push. Assert exit is non-zero, `git diff --cached --name-only` is empty, and both working changes remain.

- [ ] **Step 4: Write success and safety RED tests**

Cover these independent cases:

```text
allowed changes only -> exactly those paths committed
required path missing -> no commit
pre-existing staged change -> no commit
optional OGP missing -> allowed
manifest path uses actual auto_daily_report_YYYY_MM_DD.html name
```

- [ ] **Step 5: Run RED**

Run:

```powershell
python -m pytest -q tests/test_publish_daily_report.py
```

Expected: import or file-not-found failures because publisher and manifest do not exist.

- [ ] **Step 6: Create the exact manifest**

Use this JSON shape:

```json
{
  "required": [
    "input/day/{MMDD}.txt",
    "daily-news/data.json",
    "daily-news/index.html",
    "daily-news/archive/{YYYY-MM-DD}.html",
    "presentations/auto_daily_report.html",
    "presentations/auto_daily_report.json",
    "presentations/daily_reports/auto_daily_report_{YYYY_MM_DD}.html",
    "presentations/daily_reports/index.json",
    "presentations/daily_reports/searchable.json",
    "public-pages/api/auto_daily_report/latest.json",
    "public-pages/news/{YYYY-MM-DD}.json",
    "public-pages/news/archive_index.json",
    "public-pages/news/version.json"
  ],
  "optional": ["presentations/daily_reports/og/{YYYY_MM_DD}.png"]
}
```

- [ ] **Step 7: Implement validation before mutation**

The publisher must collect unstaged tracked changes, staged changes, and untracked files using argument-list `subprocess.run`. It must validate all conditions before invoking `git add -- <exact paths>`. It must never use `shell=True`.

- [ ] **Step 8: Implement commit and bounded push retry**

After a successful limited commit, run `git push origin HEAD:main`. On failure, run `git fetch origin main`, `git rebase origin/main`, and one final push. Abort a failed rebase and exit 1. Never force.

- [ ] **Step 9: Run GREEN**

Run:

```powershell
python -m pytest -q tests/test_publish_daily_report.py
python -m pytest -q
```

Expected: all publisher tests and full suite pass.

### Task 3: Move Windows override to a safe independent checkout

**Files:**
- Create: `scripts/run_daily_override.ps1`
- Rewrite: `scripts/run_daily_override.bat`
- Create: `scripts/register_daily_override_task.ps1`
- Create: `tests/test_daily_override_automation.py`
- Modify: `.gitignore`

**Interfaces:**
- Runner parameters: `-RepoPath`, `-PythonPath`, `-LogPath` with repo-relative defaults.
- Installer parameters: `-CheckoutPath`, `-RepositoryUrl`, `-TaskName`, `-At`, `-PlanOnly`.
- Installer `-PlanOnly` output: one JSON object with checkout, action, working directory, trigger, principal, and settings.

- [ ] **Step 1: Add exact tracking exceptions**

```gitignore
!scripts/run_daily_override.ps1
!scripts/register_daily_override_task.ps1
!tests/test_daily_override_automation.py
```

- [ ] **Step 2: Write launcher contract RED tests**

Assert the batch contains `%~dp0..`, invokes `powershell.exe -NoProfile -ExecutionPolicy Bypass`, and contains none of `C:\develop\ai-news-site` as `REPO`, `git add -u`, `git add -A`, `git reset`, or `git clean`.

- [ ] **Step 3: Write installer PlanOnly RED test**

Invoke:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/register_daily_override_task.ps1 -CheckoutPath C:\develop\ai-news-site-automation -PlanOnly
```

Parse JSON and assert daily `08:00`, task name `visionhub-daily-news-override`, `cmd.exe` action, and automation checkout working directory.

- [ ] **Step 4: Write runner safety RED tests**

Use a temporary bare origin and clone. Cover dirty tracked+untracked state being stashed, ff-only sync, manifest-only publisher invocation, unavailable Ollama not causing a preflight abort, and rebase conflict retaining the local commit/stash.

- [ ] **Step 5: Run RED**

Run:

```powershell
python -m pytest -q tests/test_daily_override_automation.py
```

Expected: new PowerShell files are missing and the legacy launcher contract fails.

- [ ] **Step 6: Implement the thin batch launcher**

The launcher derives the repo, loads external then legacy secrets without printing values, and invokes the runner:

```bat
@echo off
setlocal
for %%I in ("%~dp0..") do set "REPO=%%~fI"
if exist "%LOCALAPPDATA%\visionhub-daily-news-override\secrets.local.bat" call "%LOCALAPPDATA%\visionhub-daily-news-override\secrets.local.bat"
if not defined NVIDIA_API_KEY if exist "C:\develop\ai-news-site\scripts\secrets.local.bat" call "C:\develop\ai-news-site\scripts\secrets.local.bat"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO%\scripts\run_daily_override.ps1" -RepoPath "%REPO%"
exit /b %ERRORLEVEL%
```

- [ ] **Step 7: Implement the PowerShell runner**

Use a named mutex. If `git status --porcelain` is nonempty, run `git stash push --include-untracked --message "daily-override recovery <timestamp>"`. Fetch main, calculate ahead/behind, fast-forward or rebase, choose NVIDIA only when an `nvapi-` key is present, run the pipeline, then call the Python publisher with `--push`.

- [ ] **Step 8: Implement the idempotent installer**

In non-PlanOnly mode, clone only when the path is absent; validate `.git` and the normalized origin URL when present; register the task with `Register-ScheduledTask -Force`. Do not delete or overwrite an invalid existing path.

- [ ] **Step 9: Run GREEN and PowerShell parse checks**

Run:

```powershell
python -m pytest -q tests/test_daily_override_automation.py
powershell.exe -NoProfile -Command "$e=$null;[System.Management.Automation.Language.Parser]::ParseFile('scripts/run_daily_override.ps1',[ref]$null,[ref]$e)>$null;if($e.Count){$e|% Message;exit 1}"
powershell.exe -NoProfile -Command "$e=$null;[System.Management.Automation.Language.Parser]::ParseFile('scripts/register_daily_override_task.ps1',[ref]$null,[ref]$e)>$null;if($e.Count){$e|% Message;exit 1}"
python -m pytest -q
```

Expected: zero parser errors and all tests pass.

### Task 4: Connect cloud workflow to the safe publisher

**Files:**
- Modify: `.github/workflows/auto-daily-report-cloud-fallback.yml`
- Modify: `tests/test_daily_override_automation.py`

**Interfaces:**
- Workflow invokes `python scripts/publish_daily_report.py --date "$REPORT_DATE" --message "..." --push` after generation.
- Existing schedule and `workflow_dispatch` remain unchanged.

- [ ] **Step 1: Add a workflow contract failing test**

Assert the workflow contains `timeout-minutes: 30`, a non-cancelling concurrency group, the publisher command, and none of `git add -A`, `git add -u`, or broad directory staging.

- [ ] **Step 2: Run RED**

Run:

```powershell
python -m pytest -q tests/test_daily_override_automation.py -k cloud_workflow
```

Expected: missing timeout/concurrency/publisher assertions fail.

- [ ] **Step 3: Replace inline Git publication**

Keep provider command unchanged. Configure bot identity, compute JST date with `date +%F`, and invoke the shared publisher. Add:

```yaml
concurrency:
  group: auto-daily-report-publish
  cancel-in-progress: false

jobs:
  primary:
    timeout-minutes: 30
```

- [ ] **Step 4: Run GREEN and local workflow checks**

Run the focused test, full pytest, `git diff --check`, and search for prohibited staging commands.

### Task 5: Backfill 2026-07-17 and prepare a reviewed release commit

**Files:**
- Add: `input/day/0717.txt`
- Add: `daily-news/archive/2026-07-17.html`
- Add: `presentations/daily_reports/auto_daily_report_2026_07_17.html`
- Add: `public-pages/news/2026-07-17.json`

**Interfaces:**
- Consumes only the four named files from `C:\develop\ai-news-site`.
- Produces archive coverage for 2026-07-17 without copying current/latest/index files.

- [ ] **Step 1: Validate the dirty-source artifacts read-only**

Check every file exists, contains date `2026-07-17`, the JSON parses, and the input is nonempty. Record SHA-256 before copying.

- [ ] **Step 2: Copy only the four validated files**

Use literal source/destination paths. Do not copy directories or wildcard selections. Recompute SHA-256 and require equality.

- [ ] **Step 3: Run the complete local verification gate**

Run:

```powershell
python -m pytest -q
python -m compileall -q src scripts
git diff --check
git status --short
git diff --stat origin/main...HEAD
```

Also run both PowerShell parse checks and a temporary-repo publisher smoke test.

- [ ] **Step 4: Review scope and commit**

Stage only design/plan, `.gitignore`, named source/scripts/workflow/tests, and the four backfill files. Review `git diff --cached --name-status` before committing:

```text
fix: make daily report publishing resilient
```

### Task 6: Land, provision, recover today, and verify live

**Files/Systems:**
- Remote `awano27/ai-news-site` main.
- `C:\develop\ai-news-site-automation` independent clone.
- Task Scheduler `\visionhub-daily-news-override`.
- GitHub Actions and Pages.

- [ ] **Step 1: Re-check remote main before push**

Fetch `origin/main`. If it advanced, rebase the clean implementation branch, rerun full verification, and only then push `HEAD:main` without force.

- [ ] **Step 2: Confirm the permanent-fix commit on origin/main**

Require `git ls-remote origin refs/heads/main` to equal the pushed commit. Wait for the corresponding Pages run to finish successfully.

- [ ] **Step 3: Provision the automation clone and task**

Run the installer twice. Confirm the second run is idempotent. Export the task and verify action path, working directory, daily08:00 trigger, principal, settings, last/next run fields, and clean automation clone.

- [ ] **Step 4: Manually dispatch the fixed cloud workflow**

Use `gh workflow run auto-daily-report-cloud-fallback.yml --repo awano27/ai-news-site --ref main`, capture the new run ID, and wait for completion. Confirm logs show provider timeout followed by heuristic fallback, limited publication, commit, and push.

- [ ] **Step 5: Wait for the descendant Pages deployment**

Confirm the Pages run for the generated report commit completes successfully and deployment status is `success`/`built`.

- [ ] **Step 6: Verify archive and live latest**

Require:

```text
presentations/daily_reports/auto_daily_report_2026_07_17.html exists on main
presentations/daily_reports/auto_daily_report_2026_07_18.html exists on main
public HTML title date = 2026-07-18
public API date = 2026-07-18
cache-busted live HTML SHA-256 = raw main HTML SHA-256
cache-busted live API SHA-256 = raw main API SHA-256
```

- [ ] **Step 7: Verify the human checkout boundary**

Re-run status counts in `C:\develop\ai-news-site` and confirm no files were staged, deleted, stashed, committed, or rewritten by this implementation.

## Final Acceptance Checklist

- [ ] All new regression/integration tests were observed RED before production changes.
- [ ] Full pytest passes with zero failures.
- [ ] Both PowerShell scripts parse with zero errors.
- [ ] Prohibited Git staging/cleanup commands are absent from automation.
- [ ] New scripts/tests are tracked despite legacy ignore rules.
- [ ] Cloud fallback generates the current report when NVIDIA is unavailable.
- [ ] True empty collection fails without overwriting published content.
- [ ] Dedicated automation clone and 08:00 task are installed and idempotent.
- [ ] 2026-07-17 archive is present.
- [ ] 2026-07-18 live latest is present and byte-identical to main.
- [ ] Human dirty checkout remains untouched.
