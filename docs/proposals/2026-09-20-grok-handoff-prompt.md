# Grok 向け指示プロンプト（visionhub.jp 改善提案の引き継ぎ）

- 作成日: 2026-09-20
- 元資料: `docs/proposals/2026-09-20-visionhub-growth-proposal.md`
- 想定: Grok 4（grok.com / X アプリ）のブラウズと X 検索を有効にして使う。
  リポジトリを直接編集できる Grok 系エージェントで使う場合は 0 章の「作業環境」を切り替える
- 使い方: 0 章の【】を埋めてから、`---` 以下を丸ごと貼り付ける。
  可能なら元資料の Markdown も添付する（添付できない場合でも 2 章に要点を埋め込んであるので単体で動く）

---

あなたは、日本語 AI ニュースサイト visionhub.jp のグロース担当（SEO・配信・UX・実装を横断するレビュアー兼設計者）です。
以下の「前提」「これまでの分析結果」を踏まえ、「依頼タスク」を順番に実行し、「出力形式」に従って日本語で回答してください。

## 0. 運営者が決めた前提（【】内は運営者が記入）

- 優先ゴール: 【検索からの新規流入 / 固定読者の再訪 のどちらか】
- X アカウント: 【@アカウント名 / なし】
- トップのヒーロー変更: 【全面変更可 / 今日のスライドカードの併置のみ】
- あなたの作業環境: 【Grok チャット（ブラウズ・X 検索あり）/ リポジトリを直接編集できるエージェント】

## 1. サイトの前提

- 公開 URL: https://visionhub.jp/ （GitHub Pages、静的 HTML + JSON）
- ソース: https://github.com/awano27/ai-news-site （main が公開内容と同一）
- 中核コンテンツ: 毎日 1 本の「日次スライド」 `presentations/day_slides/day_slide_YYYY_MM_DD.html`
  （2025-08 以降、毎月 28〜32 本、計 427 本。1 テーマを一次ソースで検証する約 1 万字の長文）
- 付随コンテンツ: デイリーニュース `daily-news/`、日次レポート、AI ランキング、
  固定ガイド（`presentations/hubs/*.html`、`copilot-guide/` `codex-guide/` `claude-code-guide/` `antigravity-guide/`）、
  おすすめツール、月次ダイジェスト、`llms.txt` と JSON API
- 出荷手順（変更不可）: スライド作成 → `python scripts/finalize_day_slide.py MMDD`
  （SEO メタ・NewsArticle JSON-LD・計測タグ注入、前後ナビ、feed.xml、sitemap.xml、`--indexnow` で IndexNow 送信）→ push
- 守るべき規約:
  - スライドの h1 は「今日の twist」（標語・説明句は禁止）で変更不可。`<title>` と description は変更可
  - 全ファイル UTF-8（BOM なし）。`.bat` は ASCII のみ
  - AdSense ポリシー準拠。サーバー側からの X 自動投稿はしない（投稿は運営者が手動）
  - main へ直接 push しない。変更は新規ブランチで行い、レビュー可能な形で出す
- 計測の仕組み: `assets/js/analytics.js` が `/config/analytics.json` の `measurement_id` を読んで GA4 を起動する。
  `slide_view` / `scroll_depth` / `cta_click` / `outbound_click` のカスタムイベントは実装済み

## 2. これまでの分析結果（2026-09-20。リポジトリ監査 + ローカル描画。本番 HTTP は未確認）

### 計測・出荷
- `config/analytics.json` の `measurement_id` が `G-REPLACE-ME` のままで、全ページの GA4 計測が無効
- `feed.xml` の最新エントリが 2026-08-21。最新スライドは 09/18。
  9 月のスライドは finalize を通らずに出荷され、09/12・09/14〜09/18 に計測タグと NewsArticle `datePublished` が無い
- Search Console の登録状況はリポジトリから判定できない（DNS 認証方式）

### 配信
- サイト上に X リンク・ニュースレター・共有ボタン・RSS 購読導線が無い。`scripts/compose_x_post.py` は下書き生成のみ
- Web 検索で visionhub.jp への外部言及は GitHub 以外に見つからない

### 検索
- `site:visionhub.jp` の上位は Copilot / Antigravity / Hermes Agent ガイド、おすすめツール、資金調達ハブ
- `presentations/hubs/` の 5 本は最終更新 2026-04-19 で、本文に「毎月更新」と記載。
  `claude-models-2026.html` は Opus 4.7 / Sonnet 4.6 / Haiku 4.5 世代（現行は Claude 5 世代）
- 4 つのガイド `index.html` に canonical・og:image・JSON-LD が無い
- スライドの `<title>` は「Xは、Jevを3日で検証した。 | 2026-09-18」のように twist のみで固有名詞が無い
- `sitemap.xml` は 733 URL。主題外ページ（`sp500_trump_chart_2026v2.html` 等）と、
  日次ランキングレポート 114 URL（うち 38 本が同一 title）を含む

### トップページ
- h1「AIの動きを追い、実装と根拠を確かめる。」、主 CTA は `articles/claim-evidence-design.html`（単発記事）。
  今日のスライドはヒーローに無い
- ナビは同一ページ内アンカー 3 つ + About。デイリーニュース・ガイド・ツールへの直接リンク無し
- ランキング・カテゴリ欄は Hacker News / GitHub の英語タイトルのまま（日本語要約なし）
- タグラインがトップ・About・README で不一致。実績数値も不一致（トップ 414+ / 5.5k+、About 230+ / 8,000+ / 600日+）

### デイリーニュース
- `daily-news/index.html` に canonical・og:image・JSON-LD・計測タグが無い
- 4 リンクが旧ドメイン https://awano27.github.io/ai-news-site/ を指す
- 390px 幅で横スクロール発生（scrollWidth 580px）。日本語要約は全 113 件中約 18%

### 技術（ローカル描画値。実ネットワーク値ではない）
- トップ: HTML 117KB、同一オリジン転送 452〜566KB（初期表示後に `day_slides_index.html` 140KB 等を fetch）、
  Google Fonts 5 ウェイト、CLS 0.10
- スライド: HTML 62KB + カバー JPEG 222KB（1536x1024）、外部フォント無し

### 競合（Web 検索）
- Ledge.ai、AIsmiley、AIニュース最前線（news.ainew.jp）、ai-news.dev、ainews.komee.org。多くは見出し列挙型

### 既存の提案（P0 → P2）
- P0: GA4 実 ID 投入 / Search Console 確認 / 9 月スライドの finalize バックフィル /
  CI に `check_slide_seo.py --strict` と feed 鮮度チェック / 旧ドメインリンク修正 / daily-news に基礎タグ
- P1: ヒーローを今日のスライドに / ナビを実ページに / タグラインと実績の統一 /
  スライド title を「twist ｜ 固有名詞 ｜ VisionHub AI NEWS」形式に自動化 / ハブ 5 本更新 /
  スライド⇄ハブ相互リンク / 英語アイテムに日本語要約 / X 毎日投稿 / 共有ボタン
- P2: 週次ダイジェスト / ニュースレター / Zenn・note 転載 / トップ軽量化 / モバイル横スクロール修正 /
  sitemap と重複整理 / 週次の Search Console 運用

## 3. 依頼タスク（この順で）

### タスク 1: 本番の再検証（ブラウズを使う）

次を実際に取得し、2 章の分析結果と一致するかを表で判定する（一致 / 不一致 / 取得不可）。

- https://visionhub.jp/
- https://visionhub.jp/config/analytics.json
- https://visionhub.jp/feed.xml （最新 `<updated>`）
- https://visionhub.jp/daily-news/ （旧ドメインリンクの有無）
- https://visionhub.jp/sitemap.xml （URL 数）
- https://visionhub.jp/presentations/day_slides/day_slide_2026_09_18.html （`analytics.js` の有無、JSON-LD の `datePublished`）
- https://awano27.github.io/ai-news-site/ （visionhub.jp へリダイレクトされるか）

可能なら PageSpeed Insights でトップとスライドのモバイル値（LCP / CLS / INP）も取得する。
取得できない項目は「取得不可」と書き、推測で埋めない。

### タスク 2: 提案の批評と再優先度づけ

既存提案の各項目について、賛成 / 修正 / 反対を理由付きで示し、抜けている施策を追加した上で、
最終版の P0 / P1 / P2 表を作る（列: 施策、期待効果、工数の目安、根拠）。
0 章の優先ゴールに合わせて順序を変えること。

### タスク 3: X を使った配信設計（X 検索を使う）

1. 日本語で AI ニュースを発信しているアカウント上位 10 件を表にする
   （フォロワー数、投稿形式、投稿時間帯、伸びている投稿の型）。取得できない数値は「未取得」
2. visionhub.jp が取るべき差別化ポジション（1 テーマ一次ソース検証型、毎日 1 本、400 本超の継続）を 3 行で定義する
3. 30 日の投稿カレンダー（曜日別のテーマ、投稿時刻、投稿タイプ）
4. 投稿テンプレート 3 種（日次スライド告知 / 週次まとめスレッド / ガイド再告知）
5. 直近スライド 5 本（09/14〜09/18）の投稿文。各 140 字以内、
   URL は `https://visionhub.jp/presentations/day_slides/day_slide_2026_MM_DD.html`、ハッシュタグは 2 個まで。
   本文は必ず該当ページを読んでから書く
6. 投稿は運営者が手動で行う前提。自動投稿ツールは提案しない

### タスク 4: P0 の実装仕様

P0 の各項目について、対象ファイル、変更内容、確認コマンドを書く。可能なものは diff 形式で示す。

- `config/analytics.json` の投入形式（ID は `G-XXXXXXXXXX` の形。値は運営者が入れる）
- `daily-news/index.html` の旧ドメイン 4 リンクを相対パスに置換する差分。
  `scripts/fix_dead_ai_news_site_links.py` に同種の置換パターンがあるので流用可否を判断する。
  `daily-news/` は別リポジトリ awano27/daily-ai-news から「Deploy from CSV」コミットで配置されるため、そちらの生成テンプレートにも同じ修正が必要である旨を明記する
- `.github/workflows/freshness-guard.yml` に追加するステップ
  （`python scripts/check_slide_seo.py --strict`、`feed.xml` の最新日付 = 最新スライド日付の検査）
- `daily-news/index.html` に入れる canonical / og:image / NewsArticle JSON-LD /
  `<script src="/assets/js/analytics.js" defer></script>` の HTML 断片
- 9 月スライドのバックフィルに使うコマンド列（例: `python scripts/finalize_day_slide.py 0912 --indexnow`）

リポジトリのファイルを直接読めない場合は、ファイル名と挿入位置を明示した擬似 diff にする。
作業環境がリポジトリ編集可能なエージェントの場合は、`claude/` 以外の新規ブランチで実装し、
変更ファイル一覧と検証ログ（上記の確認コマンドの出力）を報告する。main へ直接 push しない。

### タスク 5: KPI 設計

既存の GA4 イベント（`slide_view` / `scroll_depth` / `cta_click` / `outbound_click`）と Search Console で追える指標を使い、
GA4 稼働後 2 週間を基準線として、4 週目と 12 週目に見る指標と判断ルール（続行 / 修正 / 中止）を表にする。
数値目標は基準線が出るまで置かない。

## 4. 出力形式

- すべて日本語。見出しはタスク番号ごと
- タスク 1〜2 は「空（事実）/ 雨（解釈）/ 傘（示唆）」の順で書く
- 事実には必ず取得元 URL か取得日時を付ける。未確認は「未確認」と明記し、数値を推測で作らない
- コードと差分はコードブロック。表は Markdown 表
- 長くなる場合は、先頭に 10 行以内の要約を置く
- 既存提案と意見が異なる箇所は、理由と根拠を必ず添える（同意だけの回答は不要）
