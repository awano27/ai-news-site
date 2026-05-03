# TOP ページ IA 再構成 — 実装プラン

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ルート `index.html` のセクション構成を「今日のスライド最優先 → 別フォーマット → 今週 → ハイライト統合 → アーカイブ」に再編する。配色・タイポは維持し、IA だけを変える。

**Architecture:** 既存の JS fetch / 描画関数を活かしつつ、HTML の `<section>` ブロックを再配置・統合する。`featured-reports` を hero に吸収し、`ranking` と `categories` を 1 つの "Today's Highlights" にマージ。`archive` は検索 + 月別リンク + 別ページ誘導に簡素化。

**Tech Stack:** Static HTML + vanilla JS (fetch). Python 3 (検証用). 依存追加なし。

**設計ドキュメント:** `docs/plans/2026-05-03-top-ia-redesign-design.md`

**重要なファイル:**
- 編集対象: `c:/develop/ai-news-site/index.html`（2264 行・3 つの `<style>` ブロック・6 つの inline `<script>`）
- データソース（読み取りのみ・変更しない）:
  - `news/latest.json` → `news_date`, `highlight`, `sections.{tech,research,tools}`
  - `public-pages/news/archive_index.json` → `[{date,file,count}]`
  - `daily_reports/index.json` → 最新レポートメタ
  - `presentations/day_slides/day_slide_YYYY_MM_DD.html` → スライド本体

**現在の主要セクション位置（参考）:**
- `header.site-header` 1005, `nav#globalNav` 1013, `main#main` 1033
- `section.hero` 1036, `featured-reports` 1429, `ranking` 1660, `categories` 1815, `this-week` 1837, `archive` 1857, `resources` 1881, `footer` 1961

**既存 JS 関数（活用 / 改修対象）:**
- `slideUrlFor()`, `probeLatestSlide()`（line 1506-1551）— 最新スライド URL 解決
- `fetchLatest()` / `render()`（line 1790, 1779）— ranking グリッド
- `renderHero()`（line 2039）— hero 描画
- `renderWeek()`（line 2075）— 今週
- `renderCategories()`（line 2108）— カテゴリ
- `renderStats()`（line 2141）— 集計

---

## Task 0: バックアップ作成

**Files:**
- Create: `index.html.bak.20260503`

**Step 1: バックアップコピー**

```bash
cp c:/develop/ai-news-site/index.html c:/develop/ai-news-site/index.html.bak.20260503
```

**Step 2: バックアップ確認**

```bash
ls -la c:/develop/ai-news-site/index.html.bak.20260503
```
Expected: ファイルサイズ ~87KB

**Step 3: コミット**

```bash
cd c:/develop/ai-news-site
git add -f index.html.bak.20260503
git commit -m "chore: backup index.html before IA redesign"
```

---

## Task 1: Hero セクションに「今日の3本」要素を統合（削除準備）

**目的:** `featured-reports`（line 1429-1659）の中身を hero と Section 2 に分配する。今のステップでは hero 側だけ更新し、`featured-reports` は次タスクで削除する。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html`（hero の右カラム ~line 1070-1085 付近、`#heroSlideBtn` 周辺）

**Step 1: hero 内の "今日のスライドを開く" CTA を確認**

該当箇所を特定:
```bash
grep -n "heroSlideBtn" c:/develop/ai-news-site/index.html
```
Expected: line 1073 付近に `<a id="heroSlideBtn" class="btn btn-primary" href="presentations/day_slides/day_slide_2026_05_02.html">` がある

**Step 2: hero の右カラムに「サブCTA 2リンク」を追加**

`#heroSlideBtn` の閉じタグの直後に、`featured-reports` から流用する HTMLレポート / Daily News への副 CTA を追加:

```html
<div class="hero-sub-cta" aria-label="今日の別フォーマット">
  <a id="heroReportLink" class="hero-sub-link" href="daily_reports/">
    <span class="hero-sub-label">HTML レポート</span>
    <span class="hero-sub-arrow" aria-hidden="true">→</span>
  </a>
  <a id="heroDailyNewsLink" class="hero-sub-link" href="daily-news/">
    <span class="hero-sub-label">Daily News</span>
    <span class="hero-sub-arrow" aria-hidden="true">→</span>
  </a>
</div>
```

**Step 3: 必要な CSS を最初の `<style>` ブロック末尾に追加（line 1086 直前）**

```css
.hero-sub-cta { display:flex; gap:24px; margin-top:24px; flex-wrap:wrap; }
.hero-sub-link { display:inline-flex; align-items:center; gap:6px;
  color:var(--on-dark-mu); text-decoration:none; font-size:14px;
  padding:6px 0; border-bottom:1px solid var(--navy-line); transition:color .15s; }
.hero-sub-link:hover { color:var(--yellow); }
.hero-sub-arrow { transition:transform .15s; }
.hero-sub-link:hover .hero-sub-arrow { transform:translateX(2px); }
```

**Step 4: ブラウザ確認**

`file:///c:/develop/ai-news-site/index.html` を開き、hero に副リンク 2 本が表示されること

**Step 5: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "feat(top): add hero sub-CTA for report and daily news"
```

---

## Task 2: 「Today」セクション新設（旧 featured-reports を変形）

**目的:** `featured-reports` の枠は残しつつ、3 カード（slide / report / news）から **2 カード（report / daily news）** に変える。スライドは hero に集約済み。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html` line 1429-1659（`section#featured-reports`）

**Step 1: 既存 markup 構造を確認**

```bash
sed -n '1429,1465p' c:/develop/ai-news-site/index.html | head -40
```
Expected: 3 つの `.main-card`（`#todaySlideCard`, report, news）が含まれる

**Step 2: セクション h2 を変更**

旧: 「今日の 3 本 — スライド・レポート・Daily News」
新: 「今日のAI、もっと読む」

セクション ID も変更: `id="featured-reports"` → `id="today-formats"`

**Step 3: 1 番目の `.main-card.is-primary`（`#todaySlideCard`、line 1448-1495 付近）を削除**

カード 3 枚 → 2 枚に。残す 2 枚（HTMLレポートカード / Daily News カード）はそのまま流用。

**Step 4: グリッドが 2 カラムで表示されるよう CSS を確認・調整**

`featured-reports .main-grid` の `grid-template-columns` を `repeat(2, 1fr)` に。モバイルは `1fr`（縦積み）。

**Step 5: ブラウザ確認**

- セクション見出しが「今日のAI、もっと読む」
- カードが 2 枚（HTMLレポート / Daily News）並んでいる
- スライドカードは消えている（hero に集約済み）

**Step 6: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "refactor(top): convert featured-reports to 2-card today-formats"
```

---

## Task 3: 「Today's Highlights」統合セクション新設

**目的:** 既存の `#ranking`（line 1660-1814）と `#categories`（line 1815-1836）を 1 つの統合セクションにマージ。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html`

**Step 1: 新セクション markup を categories の位置（line 1815 付近）に追加**

```html
<section id="todays-highlights" class="section section-light">
  <div class="container">
    <header class="section-header">
      <h2>今日のハイライト</h2>
      <p class="section-lead">スコア上位の記事と、カテゴリ別の最新ニュース</p>
      <div class="tab-bar" role="tablist" aria-label="ハイライト切替">
        <button class="tab-btn is-active" role="tab" data-tab="ranking" aria-selected="true">ランキング TOP3</button>
        <button class="tab-btn" role="tab" data-tab="categories" aria-selected="false">カテゴリ別</button>
      </div>
    </header>
    <div class="tab-panel is-active" data-panel="ranking">
      <div id="rankingGrid" class="ranking-grid"><!-- JS が描画 --></div>
      <a class="section-link" href="ranking.html">ランキング全体を見る →</a>
    </div>
    <div class="tab-panel" data-panel="categories" hidden>
      <div id="categoriesGrid" class="categories-grid"><!-- JS が描画 --></div>
    </div>
  </div>
</section>
```

**Step 2: 旧 `#ranking` セクション（line 1660-1814、見出し + grid + script）と `#categories`（line 1815-1836）を削除**

ただし script 内のロジック（`fetchLatest`, `render`, `renderCategories`）は新セクション用に保持する（次タスク）。

**Step 3: タブ切替 JS をページ末尾の inline script に追加**

```javascript
(function() {
  var tabs = document.querySelectorAll('#todays-highlights .tab-btn');
  var panels = document.querySelectorAll('#todays-highlights .tab-panel');
  tabs.forEach(function(t) {
    t.addEventListener('click', function() {
      tabs.forEach(function(x){ x.classList.remove('is-active'); x.setAttribute('aria-selected','false'); });
      panels.forEach(function(p){ p.classList.remove('is-active'); p.hidden = true; });
      t.classList.add('is-active'); t.setAttribute('aria-selected','true');
      var target = document.querySelector('#todays-highlights .tab-panel[data-panel="'+t.dataset.tab+'"]');
      if (target) { target.classList.add('is-active'); target.hidden = false; }
    });
  });
})();
```

**Step 4: タブ用 CSS（最初の `<style>` ブロック末尾）**

```css
.tab-bar { display:flex; gap:8px; margin-top:16px; }
.tab-btn { background:transparent; border:1px solid var(--navy-line-2); color:inherit;
  padding:8px 16px; border-radius:999px; cursor:pointer; font:inherit; transition:all .15s; }
.tab-btn.is-active { background:var(--yellow); color:var(--navy); border-color:var(--yellow); }
.tab-btn:not(.is-active):hover { border-color:var(--yellow); }
.tab-panel { display:none; }
.tab-panel.is-active { display:block; }
```

**Step 5: ブラウザ確認**

- 「今日のハイライト」セクションが存在
- タブ「ランキング TOP3」「カテゴリ別」が切り替えできる
- 既存のランキング grid と categories grid の中身は次タスクで JS 修正後に表示される（今はからでOK）

**Step 6: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "feat(top): add unified todays-highlights section with tabs"
```

---

## Task 4: JS 描画関数を新構造に合わせて修正

**目的:** `fetchLatest()` と `renderCategories()` を新しい `#rankingGrid` / `#categoriesGrid` の DOM ID にバインドし直す。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html`（script ブロック line 1710-1812 と line 1992-2229）

**Step 1: ranking 描画の DOM ID を確認**

旧 `document.getElementById('rankingGrid')` (line 1780) は **そのまま**（新セクションも同じ ID を使う）。確認のみ。

**Step 2: `renderCategories(latest)` の出力先 ID を `categoriesGrid` に変更**

line 2108 の関数を編集。元の出力先（categories セクションの inner）を `#categoriesGrid` にする:

```javascript
function renderCategories(latest) {
  var grid = document.getElementById('categoriesGrid');
  if (!grid) return;
  // 既存ロジックを保持しつつ、出力先のみ差し替え
  ...
}
```

**Step 3: `renderStats` 周辺で削除セクション（旧 categories）を参照していたら除去**

旧 `#categories` 内の DOM 参照があれば null チェック追加または削除。

**Step 4: ブラウザ確認**

- ハイライト > ランキング TOP3 タブで上位 3 記事が描画される
- ハイライト > カテゴリ別タブでカテゴリ別ニュースが描画される
- DevTools Console にエラーが出ない

**Step 5: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "fix(top): rebind highlight render targets to new section ids"
```

---

## Task 5: Archive セクションを検索 + 月別リンクに簡素化

**目的:** 既存の長大なアーカイブリストを TOP から削除し、検索ボックス + 月別リンク + 別ページ CTA に置き換える。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html`（`#archive` line 1857-1880）

**Step 1: 新 markup**

```html
<section id="archive" class="section section-light">
  <div class="container">
    <header class="section-header">
      <h2>過去のすべてのAIニュース</h2>
      <p class="section-lead">日付・キーワードで遡る</p>
    </header>
    <div class="archive-search">
      <input type="search" id="archiveSearchInput" placeholder="キーワードで検索（例: GPT-5, M&A, 規制）"
             autocomplete="off" aria-label="アーカイブ検索">
      <button id="archiveSearchBtn" class="btn btn-secondary">検索</button>
    </div>
    <nav class="archive-months" aria-label="月別アーカイブ">
      <ul id="archiveMonthsList"><!-- JS が直近 6 ヶ月を描画 --></ul>
    </nav>
    <a class="section-link" href="presentations/news_archive.html">アーカイブ全件を見る →</a>
  </div>
</section>
```

**Step 2: 月別リンク描画 JS を追加**

`archive_index.json` から直近 6 ヶ月をユニーク化して描画:

```javascript
fetch('public-pages/news/archive_index.json?t='+Date.now(),{cache:'no-store'})
  .then(function(r){ return r.json(); })
  .then(function(list){
    var months = {};
    list.forEach(function(e){ var m = e.date.slice(0,7); months[m] = (months[m]||0)+1; });
    var keys = Object.keys(months).sort().reverse().slice(0,6);
    var ul = document.getElementById('archiveMonthsList');
    if (!ul) return;
    ul.innerHTML = keys.map(function(m){
      return '<li><a href="presentations/news_archive.html#'+m+'">'+m+' <span class="count">('+months[m]+')</span></a></li>';
    }).join('');
  })
  .catch(function(){});
```

**Step 3: 検索ボックス submit ハンドラ**

```javascript
var input = document.getElementById('archiveSearchInput');
var btn = document.getElementById('archiveSearchBtn');
function go(){ var q = (input.value||'').trim();
  if (q) location.href = 'presentations/news_archive.html?q=' + encodeURIComponent(q);
}
btn && btn.addEventListener('click', go);
input && input.addEventListener('keydown', function(e){ if (e.key==='Enter') go(); });
```

**Step 4: ブラウザ確認**

- アーカイブセクションが新 markup で表示
- 月別リンクに直近 6 ヶ月が出る
- 検索ボックスに何か入れて Enter → news_archive.html?q=... に遷移する（遷移先で検索が動くかは別案件、本タスクでは URL が組まれることまで確認）

**Step 5: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "feat(top): simplify archive section to search + month links"
```

---

## Task 6: ナビゲーションのアンカー更新

**目的:** ヘッダー `nav#globalNav` の各リンク（旧 `#ranking`, `#categories`）を新構造に合わせて差し替える。

**Files:**
- Modify: `c:/develop/ai-news-site/index.html` line 1013-1032 付近

**Step 1: 旧アンカーを確認**

```bash
grep -n 'href="#' c:/develop/ai-news-site/index.html | head -20
```

**Step 2: 差し替え**

| 旧 | 新 |
|---|---|
| `href="#featured-reports"` | `href="#today-formats"` |
| `href="#ranking"` | `href="#todays-highlights"` |
| `href="#categories"` | （削除 or `#todays-highlights` に統合）|

**Step 3: ブラウザ確認**

ヘッダーナビをクリックして新セクションにスクロールすること

**Step 4: コミット**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "fix(top): update nav anchors to new section ids"
```

---

## Task 7: モバイル レスポンシブ確認

**Files:** 確認のみ

**Step 1: DevTools でモバイル表示**

Chrome DevTools → Device Toolbar → iPhone 14 Pro (390x844) で開く

**Step 2: 各セクションの確認**

- Hero: タイトル → サムネイル → CTA → 副リンク の縦積み
- Today: カード 2 枚が縦積み（1fr）
- This Week: 横スクロール
- Today's Highlights: タブで切替（横並び縦積みは関係なし）
- Archive: 検索ボックス全幅、月別リンク縦並びでも横でもOK

**Step 3: 必要なら CSS メディアクエリ調整**

```css
@media (max-width: 768px) {
  .hero-sub-cta { gap:12px; }
  #today-formats .main-grid { grid-template-columns: 1fr; }
}
```

**Step 4: コミット（変更があれば）**

```bash
cd c:/develop/ai-news-site
git add index.html
git commit -m "fix(top): mobile responsive adjustments for new sections"
```

---

## Task 8: ブラウザでの最終 QA

**Files:** 確認のみ

**Step 1: ブラウザで開く**

`file:///c:/develop/ai-news-site/index.html`

**Step 2: チェックリスト**

- [ ] hero に「今日のスライドを開く」CTA がある
- [ ] hero に副リンク（HTMLレポート / Daily News）2 本がある
- [ ] hero CTA をクリック → 最新スライドが開く
- [ ] Section 2 「今日のAI、もっと読む」が 2 カードで表示
- [ ] Section 3 「今週のスライド」横スクロール動作
- [ ] Section 4 「今日のハイライト」タブ切替動作（ranking ⇄ categories）
- [ ] Section 5 「過去のすべてのAIニュース」検索ボックス + 月別 6 件
- [ ] Section 6 「リソース・ガイド」現状維持
- [ ] DevTools Console にエラーなし
- [ ] Network タブで `news/latest.json`, `archive_index.json` が 200 で取得
- [ ] モバイル表示（390x844）で全セクションが破綻なく縦積み
- [ ] ヘッダーナビのリンクが新セクションへスクロール

**Step 3: スクショ保存（任意）**

PC・モバイル両方のスクショを保存して PR に添付。

**Step 4: 最終コミット & プッシュ**

問題がなければ:

```bash
cd c:/develop/ai-news-site
git push origin main
```

---

## Task 9: メモリ更新（オプショナル）

**Files:**
- Update: `C:/Users/awano/.claude/projects/c--develop-ai-news-site/memory/MEMORY.md`

**Step 1: 既存メモリ「日次スライド作成時の更新ファイル一覧」が古くなっていれば、新セクション ID（`today-formats`, `todays-highlights`）を反映**

**Step 2: 必要なら新規メモリ追加**

例: `top_ia_2026_05_03_redesign.md` — 新 IA の意図と各セクションの役割を記録。

---

## ロールバック手順

問題が発覚したら:

```bash
cp c:/develop/ai-news-site/index.html.bak.20260503 c:/develop/ai-news-site/index.html
git add index.html
git commit -m "revert: rollback top IA redesign"
git push origin main
```

## 完了基準

- 全タスクのコミットが main にプッシュ済み
- GitHub Pages に反映後、本番 URL（https://awano27.github.io/ai-news-site/）でも Task 8 のチェックリストが全て通る
- 既存の他ページ（presentations/index.html, day_slides_index.html 等）への影響なし
