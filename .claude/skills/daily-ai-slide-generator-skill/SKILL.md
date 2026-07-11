---
name: daily-ai-slide-generator
description: 日次AIニューススライドの作成〜公開を一気通貫で行う。「MM/DDのスライドを作成」「今日のスライドを生成」「今日の最新AIニュースを検索して提案」「Xで今日のニュース候補」等、日次スライドの作成・ニュース選定を求められたら使用。commit/push まで含む。
---

# デイリーAIニューススライド生成（2026-07 改訂版）

日付指定 or 「今日のニュースから」の依頼で、ニュース選定 → スライド生成 → index 更新 → 検証 → commit/push まで完了させる。
⚠️ 旧版（PDF画像埋め込み・4ファイル更新・stash/pop）は廃止。git 履歴参照。

## Step 1: ニュースソース確定

1. `input/day/MMDDslide.txt` → `MMDD.txt` の順に確認。あればそれを使用
2. 無ければ候補を提案:
   - X の話題: **x-collect skill**（grok-build ネイティブX検索、必ず `-m grok-build`）
   - Web: 当日の主要発表を検索し、サプライズ性・実務インパクトで 3 候補提示
3. ユーザーが選定したらタイトル・要点を確定

## Step 2: スライド生成

- デザイン2系統: 既定 = **画像なし Swiss Modernism**。「一新して」「Claudeっぽく」= **Claude-warm**（cream/clay/serif、06/05 Miso One 回がテンプレ）
- **最新の `presentations/day_slides/day_slide_*.html` をコピーして** `--accent` 1色のみ変更（カラーは直近スライドと被らない色）
- ヒーロー見出し: `clamp(34px, 5.2vw, 66px)` + `text-wrap: balance` + `align-items: start`
- h1 は「製品の一言紹介」形式（例: `TimesFM：1000億データ点で学んだ「未来予測AI」`）

### 生成後の必須チェック
```bash
rtk grep "max-width:\s*\d+ch" presentations/day_slides/day_slide_2026_MM_DD.html
# → 0件であること（ch単位 max-width は日本語で早折り返しバグ。過去2回再発）
```

## Step 3: サイト統合（実質3ファイル + sitemap）

| ファイル | 更新内容 |
|---|---|
| `presentations/day_slides/day_slide_2026_MM_DD.html` | 新規 |
| `presentations/day_slides_index.html` | 月の件数 +1。**feat-card と slide-card の両方**に追加（list/hub は両セレクタを収集して描画）。**feat-title は短い正式タイトルのみ**（本文・デザインメモ貼付禁止） |
| `presentations/day_slides/images/MMDD/cover.jpg` | OG 用カバー |
| `sitemap.xml` | `python scripts/build_sitemap.py`（自動再生成されないので毎回実行） |

- 統合後に冪等スクリプトを再実行: `python scripts/inject_slide_nav.py` + `python scripts/update_home_fallback.py`

- `presentations/index.html` / `day_slides_list.html` / ルート `index.html` は**自動描画＝更新不要**
- index の統計件数がドリフトしていたら実カード数で是正

## Step 4: 検証

1. スライドをブラウザ/Playwright スクリプトで開き、レイアウト崩れ・リンク・mojibake を確認（証跡: ログ/スクショ保存）
2. `python scripts/check_site_freshness.py` で index/sitemap 伝播を確認（push 後は /site-verify skill）

## Step 5: コミット & プッシュ（ユーザー確認は1回だけ）

```bash
rtk git add presentations/day_slides/day_slide_2026_MM_DD.html presentations/day_slides_index.html presentations/day_slides/images/MMDD/ sitemap.xml
rtk git commit -m "add: [Topic] slide (MM/DD)"
rtk git pull --rebase origin main && rtk git push origin main
```

- rebase で自動生成ファイル（daily-news/*, auto_daily_report.*, version.json, latest.json, archive_index.json）が衝突したら **`git checkout --ours`**（= リモート側採用）→ `git add` → `git rebase --continue`
- behind が大きい/dirty が複雑な場合は stash/pop 禁止。origin/main の detached worktree に cherry-pick → push

### 完了条件（"push した" ではなく "origin/main に載った" を検証）

```bash
rtk git fetch origin main && git cat-file -e origin/main:presentations/day_slides/day_slide_YYYY_MM_DD.html && echo OK
```

- ⚠️ **Claude cloud/web セッションは `claude/*` ブランチに push する**（main ではない）。上のチェックが FAIL する場合は PR マージまでがこのスキルの完了条件（2026-06-30 / 07-02 はマージ漏れでサイトから消失した実績あり）
- 検知網: `python scripts/check_site_freshness.py`（直近14日の歯抜けを CRITICAL 検出）+ `python scripts/check_orphaned_slide_branches.py`（未マージ claude/* ブランチの孤立スライド検出）。両方 freshness-guard.yml で毎朝 CI 実行される
- 完了報告: `https://visionhub.jp/presentations/day_slides/day_slide_YYYY_MM_DD.html`
