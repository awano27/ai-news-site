# CLAUDE.md

ai-news-site (visionhub.jp) — AIニュースの自動収集・日次レポート・日次スライド生成、GitHub Pages 公開。
最終改訂: 2026-07-11（日次手順にスライドナビ注入・home fallback 更新を追加。2025年版の旧手動ワークフローは git 履歴参照）

## アーキテクチャ（2026-07 現在）

- **データ生成の本体は `src/auto_collect`**（2026-04-25 リアーキテクト以降）。外部サイトのスクレイプは廃止
- 日次レポートは **cloud-primary 構成**: GitHub Actions が 06:00 JST に生成（X 空）→ 08:00 ローカル override が X 入りで上書き（Windows Task Scheduler `visionhub-daily-news-override`）
- daily-news/ も同パイプラインが生成。X ブックマークは Obsidian vault から直読み
- レポートアーカイブ: `presentations/daily_reports/index.json`（html_report 実行時に自動再生成）
- トップ #categories: `news/latest.json` の sections ← build-homepage-latest.js が auto_daily_report/latest.json から生成
- AI Ranking ページ: `build-ranking-preview.yml` が 08:30 JST に日次自動更新
- CI ガード: `freshness-guard.yml`（最新スライドの index/sitemap 伝播監視 + daily-news の X 欠落を2日連続で検知＝`check_x_freshness.py`）、mojibake-guard、pages-heal

## 日次スライド作成（最重要ワークフロー）

デザインは2系統。既定は**画像なし Swiss Modernism エディトリアル**、「一新して」「Claudeっぽく」と言われたら **Claude-warm**（cream paper・clay accent・serif、06/05 Miso One 回がテンプレ）。

1. **最新の `presentations/day_slides/day_slide_*.html` をテンプレに**、`--accent` 1色のみ変更して新規作成
   - `h1` = 今日の twist（標語禁止。「今日のAIを5分で」や名詞句の説明は置かない）
   - `meta name="description"` = 開ループ1文（理由・仕組みは書かない）
   - `p.lead` = 回収（仕組み・だから何）。トップの h1 はスライド h1 をそのまま写す
2. 更新は実質 **3ファイルのみ**:
   - `presentations/day_slides/day_slide_2026_MM_DD.html`（新規）
   - `presentations/day_slides_index.html`（月の件数 +1、リスト先頭に `<li>`。feat-title は**短い正式タイトルのみ**——本文貼付禁止）
   - `presentations/day_slides/images/MMDD/cover.jpg`（OG 用）
3. `presentations/index.html`・`day_slides_list.html`・ルート `index.html` は day_slides_index.html / archive_index.json から**自動描画＝更新不要**
4. ヒーロー見出しは `clamp(34px, 5.2vw, 66px)` + `text-wrap: balance`（旧 clamp(42,7.4vw,96px) は日本語見出しが破綻）
5. index の統計件数はドリフトするので実カード数で是正
6. push 前に `python scripts/inject_slide_nav.py` と `python scripts/update_home_fallback.py` を実行（build_sitemap.py と同列・冪等）。2026-07-11 UX改善で全 day_slide に前日/翌日ナビが `<!-- slide-nav:start/end -->` マーカーで注入されるため、テンプレコピーで混入した古いナビの是正と、前日側スライドの「翌日→」リンク更新の両方をこれが行う
7. sitemap は `python build_sitemap.py`（day-slide コミットでは自動再生成されない）
8. 3ファイル + ナビ/フォールバック更新分 + sitemap を同一コミットで push

## 規約

- 全ファイル UTF-8（BOM なし）。mojibake は専用 fix スクリプトあり
- `.bat` / `.cmd` は **ASCII のみ**（日本語 Windows の CP932 問題）
- 動作確認は **Playwright スクリプト＋ログ・スクショ保存**（MCP 対話操作ではなくターミナル実行で証跡を残す）
- rebase で自動生成ファイルが衝突したら **`--ours`**（= リモート側を採用）: daily-news/*, auto_daily_report.*, version.json, latest.json
- `.gitignore` が .github/ script/ scripts/ の新規ファイルをブロック → 新規追加は `git add -f`
- behind + dirty の状態で特定ファイルだけ deploy する時: stash→rebase→pop は禁物。origin/main の detached worktree に cherry-pick → push
- **Claude cloud/web セッションは `claude/*` ブランチに push する**。成果物は origin/main 到達（`git cat-file -e origin/main:<path>`）までが完了条件。孤立スライド検知は `scripts/check_orphaned_slide_branches.py`（freshness-guard.yml で毎朝実行）

## 復旧手順（要点）

- cron 不発: `gh workflow run auto-daily-report-cloud-fallback.yml`
- daily-news の X 欠落: `Get-ScheduledTask visionhub-daily-news-override` で診断 → `cmd /c scripts\run_daily_override.bat`。切り分けは `where python` の先頭と run.err 末尾を先に見る（hermes venv の PATH 奪取が主因）
- サイト検証: `/site-verify` skill（`scripts/check_site_freshness.py` + curl + `gh run list`）
- Pages asset 404: memory `github_pages_asset_404_fix.md` の1コマンド復旧

## データ形式（参考）

`input/day/MMDD.txt` → `news/YYYY-MM-DD.json` → `public-pages/news/`（archive_index.json / version.json）。
archive_index は実 JSON より先行して 404 リンクを抱えるドリフトが既知（origin 基準で再生成 + fileless 日付 drop で修復）。
詳細仕様・旧手動フロー（4ファイル更新・画像 hero 等）は 2026-07-07 以前の git 履歴の CLAUDE.md を参照。
