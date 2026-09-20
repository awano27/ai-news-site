# visionhub.jp 閲覧者を増やすための改善提案（2026-09-20）

- 対象: https://visionhub.jp/（リポジトリ `awano27/ai-news-site` の `main` = 公開ソース）
- 目的: 新規訪問者の獲得と、再訪の定着（「もっとユーザーが見てくれる」状態）
- 分析方法: リポジトリ内の公開 HTML / JSON / スクリプト / ワークフローの静的監査、
  Playwright（Chromium）によるローカル描画（デスクトップ 1440x900、モバイル 390x844）、
  Web 検索によるインデックス状況・競合の確認
- 制約: 実行環境の egress ポリシーで `visionhub.jp` への直接アクセスが遮断されていたため、
  本番の応答ヘッダ・実ネットワークでの読み込み時間・GA4/Search Console の実データは未確認。
  数値はすべて `main` の内容とローカル描画から得たもの

---

## 0. 結論（先に要点）

サイトは「毎日 1 本、13 か月以上途切れず出し続けている」「一次ソース検証つきの深い記事」という、
競合にはない強い資産を持っている。一方で、**その資産が読者に届く経路がほぼ整備されていない**。

1. **計測が動いていない**: GA4 の測定 ID がプレースホルダのままで、全ページの計測が無効
2. **配信が止まっている**: Atom フィードの最新記事が 08/21 で止まり、X・ニュースレター・共有ボタンが無い
3. **検索の資産が劣化中**: 検索に強いハブ記事の最終更新が 04/19 で、内容も 1 世代前
4. **入口が売っていない**: トップの主 CTA が設計記事 1 本を指し、毎日のスライドが主役になっていない
5. **出荷手順の抜け**: 9 月のスライドが finalize 未実行で出荷され、SEO/計測/フィードが静かに退行

最初の 1 週間で 1〜2 と 5 を止血し（作業量は小さい）、続く 4 週間で 3〜4 に手を入れるのが最短経路。

---

## 1. 空（事実）

### 1-1. 計測

| 項目 | 事実 | 根拠 |
|---|---|---|
| GA4 測定 ID | `config/analytics.json` の `measurement_id` が `G-REPLACE-ME` | `assets/js/analytics.js` はプレースホルダを検出すると no-op になる |
| 計測タグの網羅率 | 804 ページ中 790 に注入済み（98.3%） | `python scripts/check_analytics_coverage.py` |
| 未注入ページ | 09/12・09/14〜09/18 のスライド 6 本、直近のランキングレポート、`day_slides_list.html` | 同上 |
| Search Console | 設定手順書 `ops/search-console-setup.md` あり。DNS 認証方式のためリポジトリからは登録済みか判定不能 | 手順書 |
| IndexNow | 鍵ファイルと `config/indexnow.json` あり。既定は dry-run、`finalize_day_slide.py --indexnow` 実行時のみ送信 | `scripts/indexnow_ping.py` |

### 1-2. 配信（読者に届ける経路）

| 項目 | 事実 |
|---|---|
| Atom フィード | `feed.xml` の最新エントリは 2026-08-21。最新スライドは 09/18。約 1 か月分が未配信 |
| フィード生成 | `build_feed.py` は `finalize_day_slide.py` に含まれるが、9 月のスライドは finalize を通らず出荷された（後述） |
| X（Twitter） | サイト上に X アカウントへのリンク無し。`scripts/compose_x_post.py` は下書き生成のみ（手動投稿前提） |
| ニュースレター | 無し。購読・フォロー導線がトップ・スライド・一覧ページのいずれにも無い |
| 共有ボタン | スライドページに無し（印刷・HTML 保存ボタンはある） |
| 二次掲載 | `ops/zenn-cross-post-template.md` はあるが、Web 検索で visionhub.jp への外部言及は GitHub 以外に見つからず |
| 機械可読 | `llms.txt`、`news/latest.json`、`api_docs.html` あり（エージェント向けは整備済み） |

### 1-3. 検索流入（SEO）

| 項目 | 事実 |
|---|---|
| インデックス状況 | `site:visionhub.jp` の上位は Copilot / Antigravity ガイド、Hermes Agent ガイド、おすすめツール、資金調達ハブ、日次スライドの一部 |
| ハブ記事の鮮度 | `presentations/hubs/*.html` 5 本すべて「最終更新 2026-04-19」。本文には「毎月更新」「四半期ごとに更新」と記載 |
| ハブ記事の内容 | `claude-models-2026.html` は Opus 4.7 / Sonnet 4.6 / Haiku 4.5 世代の比較。9 月のスライドは Claude 5 世代・GPT-5.6/6 を扱っており 1 世代ずれている |
| ガイド索引の SEO タグ | `copilot-guide` `codex-guide` `claude-code-guide` `antigravity-guide` の各 `index.html` に canonical・og:image・JSON-LD が無い |
| 重複タイトル | 「よくある落とし穴 \| AIエージェント構築ガイド」が 2 ページで同一。`day_slides_index.html` と `day_slides_list.html` が同じ「日次スライド一覧」 |
| スライドの title | 「Xは、Jevを3日で検証した。 \| 2026-09-18」のように twist のみ。固有名詞（TypeSafe AI など）は description にしか無い |
| Discover 適合 | 442 ページ中、JSON-LD / description / canonical / og:image / twitter:card は全件合格。`max-image-preview:large` 欠落 6 件 |
| 直近スライドの構造化データ | 09/14〜09/18 の 5 本で NewsArticle `datePublished` 欠落（`check_slide_seo.py` エラー 12 件） |
| サイトマップ | 733 URL。`sp500_trump_chart_2026v2` `infra_plan_proposal` `index_modern` `integrated_report` など主題外・レガシーページを含む。日次ランキングレポートが 114 URL あり、うち 38 本が同一 title「AIニューステクノロジーランキング・レポート」 |
| 旧ドメイン残存 | `daily-news/index.html` の「Hub に戻る」等 4 リンクが `https://awano27.github.io/ai-news-site/` を指す |

### 1-4. トップページ（入口）

| 項目 | 事実 |
|---|---|
| h1 | 「AIの動きを追い、実装と根拠を確かめる。」 |
| 主 CTA | 黄色ボタン「設計記事と再現コードを読む」→ `articles/claim-evidence-design.html`（単発記事 1 本）。副 CTA「最新ニュースを見る」→ `daily-news/` |
| 今日のスライド | ヘッダー右上のピルと、2 画面目「目的から読む」カード 01 から到達。ヒーローには無い |
| ナビ | 「今週のスライド / ランキング / リソース」（同一ページ内アンカー）+ About。デイリーニュース・ガイド・ツールへの直接リンク無し |
| ヒーロー画像 | マックス・プランクの肖像（1938 年） |
| ランキング欄 | 1 位が自サイトのスライド、2〜3 位は Hacker News の英語タイトル（日本語要約なし） |
| カテゴリ欄 | 「prism-ml/Ternary-Bonsai-2-27B-gguf」「affaan-m/ECC」などリポジトリ名がそのまま表示。`news/latest.json` の `blurb` が `title` と同一 |
| ページ高さ | デスクトップ 6,736px、モバイル 8,986px。リソース・ガイド（検索に強い固定ページ群）は最下部 |
| タグライン | トップ「AIの動き、実装と根拠を確かめる」、About の title「AIの最前線を5分で」、README「AIの最前線を5分で」 |
| 実績数値 | トップ「414+ スライド / 5.5k+ ニュース」、About「230+ スライド / 8,000+ ニュース / 600日+」 |
| 最新性表示 | 09/20 時点で最新スライドは 09/18（「2日前」表示）。09/19 号は未出荷 |

### 1-5. デイリーニュース（`daily-news/`）

| 項目 | 事実 |
|---|---|
| SEO タグ | canonical・og:image・JSON-LD・計測タグのいずれも無し（アーカイブ側 `daily-news/archive/*.html` には canonical と計測あり） |
| 言語 | `daily-news/data.json` 113 件のうち日本語要約を持つのは約 18%。ソースは HN 41、GitHub Trending 20、HuggingFace 13、ITmedia 10、GIGAZINE 10、TechCrunch 9 |
| モバイル | 390px 幅で横スクロールが発生（`scrollWidth` 580px） |
| 旧ドメイン | 上記のとおり 4 リンクが github.io を指す |

### 1-6. 技術・パフォーマンス（ローカル描画値。実ネットワーク値ではない）

| ページ | HTML | 同一オリジン転送量 | 備考 |
|---|---|---|---|
| トップ（PC） | 117KB | 566KB / 10 リクエスト | 初期表示後に `day_slides_index.html`（140KB）、`archive_index.json`（44KB）等を fetch。CLS 0.101 |
| トップ（モバイル） | 117KB | 452KB / 9 リクエスト | ヒーロー画像はモバイル用 WebP（47KB）に切替済み |
| スライド 09/18 | 62KB | 284KB / 2 リクエスト | カバー JPEG 222KB（1536x1024）。外部フォント無し。本文約 1 万字、モバイル高さ 20,616px |
| スライド一覧 | 140KB | 144KB | 421 内部リンク、画像なし |
| デイリーニュース | 123KB | 123KB | DOM ノード 3,460 |

- Google Fonts: トップと一覧ページで Noto Sans JP を 5 ウェイト（300/400/500/700/900）読み込み
- CSP・canonical・OG・JSON-LD（WebSite + SearchAction）・skip link など基礎は整っている
- 内部リンク切れ: トップ・スライド・一覧・About・ツールで 0 件（JS テンプレート文字列を除く）

### 1-7. 発行ペースと競合

- スライドは 2025-08 以降、毎月 28〜32 本（427 ファイル）。連続性は競合と比べて突出
- Web 検索で見える日本語の日次 AI ニュース系: Ledge.ai、AIsmiley、AIニュース最前線（news.ainew.jp）、ai-news.dev、ainews.komee.org。
  多くは「見出しの束」型で、visionhub の「1 テーマを一次ソースで厚く検証」型は差別化できている

---

## 2. 雨（解釈）

1. **「作る力」に対して「届ける力」が極端に弱い。** 日次生産の仕組みは成熟しているが、
   計測ゼロ・フィード停止・SNS 導線ゼロ・外部言及ゼロで、増えた読者を検知も維持もできない。
   PV が伸びないのは記事の質ではなく、到達経路の欠落が主因である可能性が高い。
2. **検索の稼ぎ頭が放置されている。** インデックス上位はガイド・ハブ・ツールカタログなのに、
   ハブは 5 か月更新なしで内容も旧世代。検索者は「2026 最新比較」を期待して着地し、
   旧モデル名を見て離脱すると考えられる（E-E-A-T の「最新性」を自ら損ねている）。
3. **日次スライドは常連向けに最適化され、検索向けではない。** twist 見出しは再訪者には効くが、
   `<title>` に固有名詞が無いと検索・SNS のスニペットで内容が伝わらない。h1 の方針（CLAUDE.md）を
   変えずに、title/description だけ検索向けに整えられる余地がある。
4. **トップが初見客に価値を説明できていない。** 主 CTA が単発の設計記事、ヒーローが物理学者の肖像で、
   「毎朝 1 本の検証済みスライド」というサイトの中核商品が画面 2 枚目以降にある。
   タグラインと実績数値がページ間で食い違い、信頼の一貫性も欠く。
5. **日本語読者に英語の生データを見せている。** ランキング・カテゴリ・デイリーニュースの大半が
   英語タイトルのままで、日本語で読む価値を提供できていない。ここは LLM 要約で低コストに埋められる。
6. **9 月の出荷が手順から外れ、退行が検知されていない。** finalize 未実行（計測タグ・datePublished・フィード）を
   CI が止めていないため、最も読まれるはずの最新記事ほど整備が薄い、という逆転が起きている。

---

## 3. 傘（提案）

優先度は「効果 ÷ 工数」。P0 は今週中、P1 は 4 週間以内、P2 は 3 か月以内を想定。

### P0 止血（合計 1 日以内）

| # | 施策 | 具体策 | 効果 |
|---|---|---|---|
| P0-1 | **GA4 を動かす** | GA4 プロパティ作成 → `config/analytics.json` に実 ID を投入 → `check_analytics_config.py` で確認。`ops/ga4-setup-guide.md` の手順どおり | 以後のすべての判断の土台。着地ページ・流入元・スクロール深度・CTA クリックが取れる |
| P0-2 | **Search Console / Bing 登録の確認** | 未登録なら DNS TXT で登録、`sitemap.xml` 送信。既登録なら「ページ」タブで除外理由の上位 3 件を確認 | 検索クエリと CTR が見える |
| P0-3 | **9 月スライドの finalize バックフィル** | 09/12・09/14〜09/18 に `python scripts/finalize_day_slide.py MMDD --indexnow` を実行し、計測タグ・datePublished・ナビ・feed・sitemap を回復 | フィード復旧、Discover 適合、計測の穴埋め |
| P0-4 | **finalize を CI で強制** | `freshness-guard.yml` に `check_slide_seo.py --strict` と `feed.xml` 最新日付 = 最新スライド日付の検査を追加し、PR で失敗させる | 退行の再発防止 |
| P0-5 | **旧ドメインリンクの修正** | `daily-news/index.html` の github.io 4 リンクを相対パスへ。生成テンプレート側も修正 | 読者を旧ドメインへ逃がさない |
| P0-6 | **デイリーニュースの基礎タグ** | canonical・og:image・NewsArticle JSON-LD・計測タグを `daily-news/index.html` に注入（既存 injector を流用） | 毎日更新される高頻度ページを検索・共有可能に |

### P1 入口と検索資産（4 週間）

| # | 施策 | 具体策 | 効果 |
|---|---|---|---|
| P1-1 | **トップのヒーローを「今日のスライド」にする** | 主 CTA = 最新スライド、カバー画像（`images/MMDD/cover.jpg`）と要点 3 行を表示。設計記事は「実装を確かめる」カードへ降格。2026-05-03 の IA 設計書（A 案）の方向に戻す | 初見客に中核商品を 1 画面で提示。直帰の減少 |
| P1-2 | **ナビの再設計** | 「今日のスライド / スライド一覧 / デイリーニュース / ガイド / ツール / About」の実ページリンクに変更。フッターに RSS・X・ニュースレターの購読導線 | 回遊と検索エンジンのクロール導線 |
| P1-3 | **タグラインと実績の統一** | 「AIの最前線を5分で」に寄せるか新タグラインに寄せるかを決め、トップ・About・README・OG を一致。実績数値は `archive_index.json` から自動算出 | 信頼の一貫性 |
| P1-4 | **スライド title/description の検索最適化** | `<title>` を「twist ｜ 固有名詞 2〜3 語 ｜ VisionHub AI NEWS」形式に。`inject_seo_meta.py` に固有名詞抽出（description や eyebrow から）を追加。h1 は現行方針のまま | 検索スニペットと SNS カードで内容が伝わる |
| P1-5 | **ハブ記事 5 本の更新** | Claude 5 世代・現行料金へ改訂、「最終更新」を実日付に。更新できないものは「毎月更新」表記を外す | 上位表示中ページの離脱抑制、順位維持 |
| P1-6 | **スライド ⇄ ハブの相互リンク** | 各スライド末尾に「関連ガイド 1 本 + 関連スライド 3 本」を `build_internal_links.py` で自動挿入。ハブ側に「このテーマの最新スライド」を自動掲載 | 内部リンクで検索評価を循環、回遊率向上 |
| P1-7 | **日本語要約の付与** | `auto_collect` で英語アイテムに 1〜2 文の日本語要約を生成し `blurb` に格納。トップのランキング・カテゴリ・デイリーニュースで表示。ランキング 1 位に自サイトのスライドを固定しない | 日本語読者にとっての「読む理由」 |
| P1-8 | **X の毎日投稿を運用に組み込む** | `compose_x_post.py` の下書きを finalize の出力に含め、出荷時に投稿。週 1 で「今週の 7 枚」スレッド。サイトにアカウントリンク | 再訪の主経路。手動でもよい |
| P1-9 | **共有ボタン** | スライドとデイリーニュースに X / LINE / コピー用リンクを追加（`data-cta` で計測） | 読者経由の拡散 |

### P2 定着と伸長（3 か月）

| # | 施策 | 具体策 | 効果 |
|---|---|---|---|
| P2-1 | **週次ダイジェスト** | `build_monthly_digest.py` を週次にも対応させ「今週のAIニュース（YYYY-WW）」を自動生成。X スレッドと Zenn/note 転載の単位にする | 「今週のAIニュース」系の検索意図を獲得、共有しやすい単位 |
| P2-2 | **ニュースレター** | 週次ダイジェストをメール配信（無料枠の配信サービスで可）。フッターとスライド末尾に登録フォーム | RSS を使わない層の再訪 |
| P2-3 | **Zenn / note 二次掲載の実行** | 既存テンプレートで月次ダイジェストとハブ記事を転載。canonical を明記 | 被リンクとリファラ流入 |
| P2-4 | **トップの軽量化** | 「今週のスライド」用に 7 件だけの JSON を生成し、140KB の `day_slides_index.html` fetch をやめる。フォントを 3 ウェイトに削減。動的挿入部にプレースホルダ高さを設定して CLS を抑える | モバイル体感速度、Core Web Vitals |
| P2-5 | **デイリーニュースのモバイル修正** | 横スクロール要因の特定と `overflow-x` 対策 | モバイル離脱の抑制 |
| P2-6 | **サイトマップと重複整理** | 主題外・レガシーページを sitemap から除外、`day_slides_list.html` と `day_slides_index.html` の役割分担（片方を canonical に）、重複タイトルの解消 | クロール予算の集中 |
| P2-7 | **計測に基づく改善ループ** | `ops/search-console-weekly.md` を毎週実行し、2 ページ目のクエリを 1 本ずつ強化 | 継続的な検索伸長 |

---

## 4. ロードマップと KPI（案）

| 期間 | 到達状態 | 確認方法 |
|---|---|---|
| 1 週目 | GA4 稼働、GSC 登録済み、feed.xml が最新スライド日付、9 月スライドに計測タグ、旧ドメインリンク 0 | `check_analytics_config.py`、`check_slide_seo.py --strict`、GSC サイトマップ「成功」 |
| 4 週目 | 新トップ公開、ナビ刷新、ハブ 5 本更新、スライド title 形式変更、X 毎日投稿開始 | GA4 のトップ CTA クリック率、スライドページ着地数 |
| 12 週目 | 週次ダイジェスト・ニュースレター運用、Zenn/note 転載 3 本以上 | GSC クリック数・表示回数、購読者数、リファラ流入 |

KPI の目標値は GA4 稼働後の最初の 2 週間を基準線として設定する（現時点では基準がないため数値目標は置かない）。

---

## 5. 確認したいこと

1. ゴールは「検索からの新規流入」と「固定読者の再訪」のどちらを優先するか（P1 の順序が変わる）
2. X アカウントは運用中か。運用中ならサイトへの導線追加と投稿の定型化から着手できる
3. トップのヒーロー（プランク肖像・設計記事 CTA）は意図的なブランディングか。意図的なら P1-1 は「ヒーロー内に今日のスライドカードを併置」に弱める
4. GA4 と Search Console の実データがあれば、本提案の優先度を数値で裏づけ直せる

---

## 付録 A. 監査に使ったコマンド

```
python scripts/check_analytics_coverage.py
python scripts/check_discover_readiness.py
python scripts/check_slide_seo.py
python -m http.server 8765   # ローカル描画用
node audit.js                 # Playwright: 4 ページ × 2 ビューポートの計測とスクリーンショット
```

## 付録 B. 関連する既存資産（新規開発せずに使えるもの）

- `scripts/finalize_day_slide.py`（SEO/JSON-LD/計測注入、ナビ、feed、sitemap、IndexNow）
- `scripts/inject_seo_meta.py` / `inject_newsarticle_jsonld.py` / `inject_analytics.py`
- `scripts/build_internal_links.py` / `build_monthly_digest.py` / `compose_x_post.py` / `generate_og_images.py`
- `ops/ga4-setup-guide.md` / `search-console-setup.md` / `search-console-weekly.md` / `zenn-cross-post-template.md`
- `docs/plans/2026-05-03-top-ia-redesign-design.md`（トップ IA の A 案）
