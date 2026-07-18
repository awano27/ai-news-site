# Auto Daily Report Reliability Design

## 目的

`https://visionhub.jp/presentations/auto_daily_report.html` を、PCやNVIDIA NIMの一時障害、開発用checkoutのdirty状態に左右されず毎日更新する。

2026-07-18時点の障害は、次の独立した2経路が同時に停止したことで発生している。

- GitHub Actionsのcloud primaryは、NVIDIA health-checkの30秒タイムアウト後に `src.auto_collect.main` が終了コード1で停止する。
- Windowsの08:00 local overrideは、人間用 `C:\develop\ai-news-site` の未追跡ファイルと `origin/main` が衝突し、生成前のrebaseで停止する。
- GitHub Pages自体は正常であり、古い2026-07-16成果物を正常に配信している。

## 採用方式

### Cloud primary

NVIDIA providerが利用不能でも、既存の `LLMProcessor` が持つ決定論的heuristic fallbackへ進む。記事とGitHub Trendingがともに空の「真の収集失敗」だけは非ゼロ終了とし、古い正常成果物を空データで上書きしない。

Cloudの生成後は、共有manifestに列挙された公開成果物だけをstageする。manifest外の変更が1件でもあればcommit/pushせず失敗させる。`git add -A`、`git add -u`、ディレクトリ全体のstage、force-pushは禁止する。

### Windows local override

本番タスクは、人間用checkoutやその共通 `.git` に依存しない独立clone `C:\develop\ai-news-site-automation` で動かす。実装作業用の隔離worktreeとは別物である。

起動時に専用cloneがdirtyなら、削除やresetをせず、日時付きstashへ追跡済み・未追跡の両方を保存する。その後 `origin/main` をfetchし、behind-onlyならfast-forward、local commitがあればrebaseする。衝突時はabortしてcommitとstashを残す。

OllamaまたはNVIDIAが利用不能でもrunnerは事前abortせず、Python pipelineのheuristic fallbackに任せる。生成後はcloudと同じmanifest/publisherを使う。

### タスク登録

追跡対象のPowerShell installerを追加する。installerは次を満たす。

- clone先が存在しなければ `origin/main` をcloneする。
- 既存先が非Gitまたは別remoteなら、削除・上書きせず拒否する。
- 再実行しても同じ08:00 JSTのTask Scheduler設定へ収束する。
- actionは `cmd.exe` 経由で専用clone内のbatch launcherを実行する。
- 現行どおりInteractiveTokenを使い、Git Credential Managerやユーザー秘密情報へのアクセスを維持する。
- `StartWhenAvailable`、`IgnoreNew`、バッテリー動作許可、1時間制限を設定する。

## コンポーネント境界

### `src/auto_collect/main.py`

- provider生成とfallback選択を担う。
- provider unavailableはwarningであり、収集済みデータがある限り処理を継続する。
- headlineとGitHubがともに空なら終了コード1とする。

### `scripts/daily_report_paths.json`

日付テンプレートを持つ唯一の公開対象manifestとする。必須パスは以下。

- `input/day/{MMDD}.txt`
- `daily-news/data.json`
- `daily-news/index.html`
- `daily-news/archive/{YYYY-MM-DD}.html`
- `presentations/auto_daily_report.html`
- `presentations/auto_daily_report.json`
- `presentations/daily_reports/auto_daily_report_{YYYY_MM_DD}.html`
- `presentations/daily_reports/index.json`
- `presentations/daily_reports/searchable.json`
- `public-pages/api/auto_daily_report/latest.json`
- `public-pages/news/{YYYY-MM-DD}.json`
- `public-pages/news/archive_index.json`
- `public-pages/news/version.json`

`presentations/daily_reports/og/{YYYY_MM_DD}.png` はPillow不在時に生成されないため任意とする。

### `scripts/publish_daily_report.py`

- manifestの日付展開、必須ファイル確認、Git変更一覧との突合、限定stage、commit、pushを担当する。
- 既存のstaged変更、manifest外変更、必須ファイル欠落を検知した場合は何もcommitしない。
- push競合時はfetch/rebase後に1回だけ再試行する。force-pushは行わない。

### `scripts/run_daily_override.ps1`

- mutex、ログ、dirty退避、Git同期、provider選択、pipeline実行、publisher呼び出しを担当する。
- ファイル削除、hard reset、cleanは行わない。

### `scripts/run_daily_override.bat`

- Task Scheduler互換の薄いlauncherとする。
- `%~dp0..` からrepo rootを求め、固定の人間用checkout pathを持たない。

### `scripts/register_daily_override_task.ps1`

- 専用cloneのprovisionとTask Scheduler登録だけを担当する。
- `-PlanOnly` では変更せず、登録予定をJSONで返す。

## 方式比較

1. 独立clone（採用）: working tree、stash、branch metadataまで人間用repoから分離できる。ディスク使用量は増えるが最も保守しやすい。
2. linked worktree: 省容量だが人間用repoの共通 `.git`、stash、branch lock、親repo移動の影響を受ける。
3. 人間用checkoutの清掃: 現在の未コミット成果物を誤って失う危険があり、今回の要件に反する。

## 失敗時の扱い

- provider unavailable: warningを記録しheuristic fallback。
- 全収集元が空: 出力前に失敗し、既存公開物を保持。
- 実行前dirty: 日時付きstashへ保存し、stash IDをログへ記録。
- Git同期衝突: rebase abort後に停止。force操作なし。
- manifest外変更: stage/commit/pushせず、dirty状態を診断用に保持。
- push競合: fetch/rebaseして1回再試行し、それでも失敗なら停止。
- Task Scheduler多重起動: runner mutexと `IgnoreNew` の二重防止。

## 秘密情報

API keyはGit管理しない。launcherは `%LOCALAPPDATA%\visionhub-daily-news-override\secrets.local.bat` を優先し、移行期間だけ既存の `C:\develop\ai-news-site\scripts\secrets.local.bat` をfallbackとして読み込む。値はログへ出力しない。

## 一回限りの復旧

- dirtyな人間用checkoutにある2026-07-17成果物から、日付付きの3成果物（daily-news archive、daily-report archive、public news JSON）と `input/day/0717.txt` だけを検証後にbackfillする。
- 人間用checkoutのコード、latestファイル、indexファイル、その他の変更は取り込まない。
- 恒久修正を `main` へ反映後、cloud workflowを手動実行して2026-07-18版を生成する。
- Pages成功だけで完了扱いにせず、cache-busted live HTML/APIと `main` blobのSHA-256一致を確認する。

## テスト方針

- provider unavailableで実 `LLMProcessor` のheuristic結果がformatterへ渡ること。
- headline/GitHubが真に空ならprovider生成・出力前に終了コード1になること。
- temporary Git repoでmanifest内だけがstage/commitされること。
- manifest外変更、必須欠落、既存staged変更を拒否すること。
- Windows runnerがdirty leftoversをstashし、remoteを同期して限定publishできること。
- installerの `-PlanOnly` が副作用なく正しいclone path、08:00 trigger、actionを返すこと。
- PowerShell parse、全pytest、`git diff --check` を通すこと。
- Actions run、Pages deployment、公開HTML/API/hashを実環境で確認すること。

## 非対象

- RSS sourceの追加・削除やAnthropic RSS 404の修正。
- 記事ランキング、要約品質、UIデザインの変更。
- 人間用 `C:\develop\ai-news-site` の未コミット変更の整理・削除・commit。
- GitHub Pages workflowの全面再設計。

## 受入条件

- NVIDIA NIMがtimeoutしても、収集データがあれば当日レポートが生成・commit・pushされる。
- PCが停止していてもcloud primaryで当日版が公開される。
- local overrideは人間用dirty checkoutに依存せず08:00 JSTに起動する。
- local runnerはOllama停止時にもheuristic fallbackで継続できる。
- 自動commitにはmanifest外のファイルが含まれない。
- 2026-07-17がarchiveへbackfillされ、live latestは2026-07-18になる。
- 公開HTML/APIと `main` の対応blobがbyte-for-byte一致する。
- 人間用checkoutの既存変更は一切変更されない。
