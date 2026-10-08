---
name: daily-ai-slide-generator
description: 日次AIニューススライドの作成・ニュース選定・既存号の再構成を求められたときに使用。「MM/DDのスライドを作成」「今日の最新AIニュース」「Xで今日のニュース候補」「このページを作り直して」「誰のどんな課題をどう解決するか」「ONE-PAGE BRIEFを絵や図付きで」「軽い画像をHTML内に埋め込んで」が対象。
---

# デイリーAIニューススライド生成（2026-10 改訂版）

日付指定・ニュース選定・既存URLの改修に対応する。HTMLファイルの納品とサイト公開は分け、公開を依頼された場合にサイト統合・commit/pushまで実施する。
⚠️ 旧版のPDFページ丸ごと画像埋め込み・4ファイル固定更新・stash/popは廃止。今回の絵付きONE-PAGE BRIEFや軽量図解は廃止対象ではない。

## 実行モード（最初に判定）

- **課題解決型の再構成**: 「誰の課題」「深く調査」「作り直して」「絵や図」「軽い画像」「ONE-PAGE BRIEF」「HTML内に埋め込んで」等の依頼では、[課題解決型の再構成手順](references/problem-first-redesign.md)を**必須**で読む。2026-10-04号で確立した内容・図版・検証の基準を適用する。画像・再構成の明示依頼は、CLAUDE.md等の通常の画像なし既定より優先する。
- **通常の新規号**: 下記のニュース選定・既存デザイン・サイト統合を使用する。指定された参照ページやユーザーのデザイン条件を優先する。
- **画像のみの修正**: 本文の合意済み内容を維持し、画像と整合に必要な箇所だけ変更する。単一画像の返答で終わらず、依頼されたHTMLに組み込む。
- 対象URL・日付・題材が指定済みならニュースを再選定しない。既存号は同じファイルを更新し、新規号として扱わない。Skillへの保存だけを依頼された場合は、記事公開やサイト統合を行わない。

## Step 1: ニュースソース確定

1. `input/day/MMDDslide.txt` → `MMDD.txt` の順に確認。あればそれを使用
2. 無ければ候補を提案:
   - X の話題: **x-collect skill**（grok-build ネイティブX検索、必ず `-m grok-build`）
   - Web: 当日の主要発表を検索し、サプライズ性・実務インパクトで 3 候補提示
3. ユーザーが選定したらタイトル・要点を確定

## Step 2: スライド生成

- 通常新規号のデザイン2系統: 既定 = **画像なし Swiss Modernism**。「一新して」「Claudeっぽく」= **Claude-warm**（cream/clay/serif、06/05 Miso One 回がテンプレ）
- 通常新規号は**最新の `presentations/day_slides/day_slide_*.html` をコピーして** `--accent` 1色のみ変更（カラーは直近スライドと被らない色）。既存号の再構成は指定されたHTMLを起点にし、内容・構図の変更を1色変更に制限しない。
- ヒーロー見出し: `clamp(34px, 5.2vw, 66px)` + `text-wrap: balance` + `align-items: start`
- 通常新規号のh1は「製品の一言紹介」形式。課題解決型では「誰の何がどう変わるか」を先に伝え、製品名・仕様は副題や本文で補う。
- 課題解決型は冒頭のONE-PAGE BRIEF画像と本文図解をHTML内に実装する。調査・根拠区分・画像圧縮・拡大・コピー・評価計画の詳細は上記参照手順に従う。

### 生成後の必須チェック
```bash
rtk grep "max-width:\s*\d+ch" presentations/day_slides/day_slide_2026_MM_DD.html
# → 0件であること（ch単位 max-width は日本語で早折り返しバグ。過去2回再発）
```

## Step 3: サイト統合（公開依頼時）

以下の表は新規号用。既存号の改修では月の件数を増やさない。既存のfeat-card／slide-cardを必要に応じて更新し、重複追加しない。HTML納品だけの場合、この工程は実施しない。

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

課題解決型では参照手順の納品前チェックも必須。画像内蔵、390px／1440px表示、拡大・Esc・フォーカス復帰、コピー、実ファイル容量を確認し、未実施を区別する。公開前後で、作成済み・GitHub保存済み・本番反映済みを混同しない。

## Step 5: コミット & プッシュ（公開依頼時、ユーザー確認は1回だけ）

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
