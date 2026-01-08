# Daily Slide Generation Scripts - 使い方と知見

日次スライドを自動生成するための再利用可能なスクリプト集

## 📋 必要なファイル

各日付（MMDD形式）について以下のファイルを準備：

```
input/day/
├── MMDD.txt                    # テキストコンテンツ（必須）
├── MMDD.png                    # サムネイル画像（推奨）
└── MMDD-{タイトル}.pdf         # スライド資料（必須）
```

## 🚀 完全なワークフロー

```bash
# 例: 01/09のスライドを作成する場合
cd D:\ai-news-site-main

# 1. PDFを画像に変換
python scripts/convert_pdf_to_slides.py 0109

# 2. HTMLスライドを生成
python scripts/create_daily_slide.py 0109

# 3. インデックスを更新
python scripts/update_indexes.py 0109 "タイトル" "説明文"

# 4. Gitにコミット＆プッシュ
git add .
git commit -m "Add daily slide for 2026-01-09: タイトル"
git push
```

## 📝 各スクリプトの詳細

### 1. convert_pdf_to_slides.py - PDFを画像に変換

```bash
python scripts/convert_pdf_to_slides.py MMDD
```

**処理内容:**
- `input/day/MMDD-*.pdf` を検索して画像に変換
- `input/day/MMDD_slides/` に slide_001.jpg ~ slide_NNN.jpg を生成
- 高解像度（2倍ズーム）でレンダリング

**例:**
```bash
python scripts/convert_pdf_to_slides.py 0108
# → input/day/0108_slides/ に12枚の画像を生成
```

### 2. create_daily_slide.py - HTMLスライドを生成

```bash
python scripts/create_daily_slide.py MMDD
```

**処理内容:**
- `input/day/MMDD.txt` からタイトル・説明を自動抽出
- テーマを自動判定（health/tech/ai/default）
- `presentations/day_slides/day_slide_2026_MM_DD.html` を生成
- スライド画像を埋め込み

**テーマ判定ロジック:**
```python
if "health" in title or "医療" in title or "健康" in title:
    theme = "health"  # エメラルドグリーン
elif "nvidia" in title or "chip" in title or "gpu" in title:
    theme = "tech"    # NVIDIA グリーン
elif "ai" in title or "agent" in title or "agi" in title:
    theme = "ai"      # パープル・ティール
else:
    theme = "default" # ブルー
```

**テーマカラー定義:**
```python
color_themes = {
    "health": {
        "primary": "#10b981",    # エメラルドグリーン
        "accent": "#059669",
        "bg_light": "#d1fae5"
    },
    "tech": {
        "primary": "#76b900",    # NVIDIA グリーン
        "accent": "#1E5128",
        "bg_light": "#f0f8f0"
    },
    "ai": {
        "primary": "#7c3aed",    # パープル
        "accent": "#14b8a6",     # ティール
        "bg_light": "#f5f3ff"
    },
    "default": {
        "primary": "#3b82f6",    # ブルー
        "accent": "#1e40af",
        "bg_light": "#dbeafe"
    }
}
```

### 3. update_indexes.py - インデックスを更新

```bash
python scripts/update_indexes.py MMDD "タイトル" "説明文"
```

**処理内容:**
- `daily_slides_index.html` の先頭（`.slides-grid`の直後）に新しいエントリを追加
- 日付・タイトル・説明・リンクを自動生成
- 既存エントリがある場合はスキップ

**例:**
```bash
python scripts/update_indexes.py 0108 \
  "ChatGPTヘルスケア：概要と分析" \
  "OpenAIが健康・ウェルネス分野に特化した新機能を発表"
```

## 🔧 トラブルシューティング

### ❌ 問題1: GitHub Pagesが更新されない

**症状:**
```
Gitにプッシュしても https://awano27.github.io/ai-news-site/ が更新されない
daily_slides_index.html の最新エントリが反映されない
```

**原因と解決策:**

#### ① Jekyllキャッシュ問題 ✅ 解決済み

**原因:** GitHub PagesがJekyllでビルドしているが、HTMLファイルが古いバージョンでキャッシュされている

**解決策:**
1. `.nojekyll` ファイルを追加してJekyllを無効化
   ```bash
   touch .nojekyll
   git add .nojekyll
   git commit -m "Disable Jekyll"
   git push
   ```

2. `.github/workflows/pages.yml` を修正してJekyllビルドステップを削除
   ```yaml
   # ❌ 削除
   - name: Build with Jekyll
     uses: actions/jekyll-build-pages@v1

   # ✅ 追加
   - name: Upload artifact
     uses: actions/upload-pages-artifact@v3
     with:
       path: ./
   ```

#### ② GitHub Actions同時実行エラー

**症状:**
```
Canceling since a higher priority waiting request for pages exists
```

**対策:**
- `.github/workflows/pages.yml` で `cancel-in-progress: false` を確認
- 前のデプロイが完了するまで待つ（5-10分）
- 空コミットでビルドを再トリガー:
  ```bash
  git commit --allow-empty -m "Trigger rebuild"
  git push
  ```

#### ③ Gitサブモジュールエラー

**症状:**
```
No url found for submodule path '.worktrees/...' in .gitmodules
The process '/usr/bin/git' failed with exit code 128
```

**原因:** Claude Codeの作業用ディレクトリ `.worktrees/` が誤ってコミットされている

**解決策:**
```bash
git rm -r .worktrees
git commit -m "Remove .worktrees from git tracking"
git push
```

`.gitignore` に以下を追加（✅ 追加済み）:
```
.worktrees/
_review_output/
output/
workspace/
*.bak
```

#### ④ ブラウザキャッシュ

**対策:**
- **Ctrl+Shift+R** (Windows) または **Cmd+Shift+R** (Mac) でハードリロード
- シークレットモードで確認
- 5-10分待ってからリロード（GitHub Pagesのデプロイに時間がかかる）
- ブラウザのキャッシュを完全にクリア

#### ⑤ ファイルが更新されない場合の強制更新

HTMLファイルにコメントを追加して変更を検出させる：
```bash
# index.html
<!-- Updated: 2026-01-08 -->

# daily_slides_index.html
<!-- Updated: 2026-01-08 with latest slides -->
```

### ❌ 問題2: JavaScriptが最新スライドを取得できない

**症状:**
```
index.html の「最新のスライドを見る」ボタンが古い日付を指す
```

**原因:** JavaScriptのセレクタが `daily_slides_index.html` の構造と一致していない

**解決策（✅ 修正済み）:**

```javascript
// ❌ 旧セレクタ（間違い）
let first = doc.querySelector('.slides li a');
const href = first.getAttribute('href');

// ✅ 新セレクタ（正しい）
let firstCard = doc.querySelector('.slide-card');
const linkElem = firstCard.querySelector('.slide-actions a[href*="day_slide"]');
const href = linkElem.getAttribute('href');
```

**修正内容:**
- `.slides li a` → `.slide-card` + `.slide-actions a[href*="day_slide"]`
- hrefのパス処理を修正（daily_slides_index.html内のリンクは既に正しいパスなので変換不要）

### ❌ 問題3: 文字コードエラー（Windowsのみ）

**症状:**
```python
UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'
```

**原因:** Windows環境でコンソール出力に絵文字（✅など）が含まれている

**解決策:** 絵文字を削除
```python
# ❌ 絵文字を使用
print(f"✅ Conversion complete!")

# ✅ 絵文字なし
print(f"Conversion complete!")
```

## 📐 ファイル構造

```
D:\ai-news-site-main\
├── input/day/
│   ├── 0108.txt                          # テキストコンテンツ
│   ├── 0108.png                          # サムネイル
│   ├── 0108-ChatGPT_Your_Health_Partner.pdf
│   └── 0108_slides/
│       ├── slide_001.jpg
│       ├── slide_002.jpg
│       └── ...
├── presentations/day_slides/
│   ├── day_slide_2026_01_08.html         # 生成されたスライド
│   └── ...
├── daily_slides_index.html               # スライド一覧ページ
├── index.html                            # トップページ
├── scripts/
│   ├── convert_pdf_to_slides.py          # PDF→画像変換
│   ├── create_daily_slide.py             # HTMLスライド生成
│   ├── update_indexes.py                 # インデックス更新
│   ├── SLIDE_GENERATION.md               # このファイル
│   └── README.md                         # JSON生成スクリプトの説明
├── .nojekyll                             # Jekyll無効化（重要！）
└── .github/workflows/
    └── pages.yml                         # GitHub Pages デプロイ設定
```

## 📦 依存関係

```bash
pip install PyMuPDF
```

- Python 3.x
- PyMuPDF (fitz): PDF処理ライブラリ

## 🎯 ベストプラクティス

### 1. テキストファイル（MMDD.txt）の形式

```
タイトル：概要と分析
エグゼクティブサマリー
本文の内容...（最初の150文字程度が自動的にsubtitleとして使用される）
```

**重要:**
- 1行目: タイトル（「：概要と分析」などは自動削除される）
- 2行目: 通常は「エグゼクティブサマリー」
- 3行目以降: 本文（最初の文が説明として抽出される）

### 2. PDF命名規則

```
MMDD-{英語タイトル}.pdf

例:
0108-ChatGPT_Your_Health_Partner.pdf
0107-Rubin_Redefining_the_AI_Factory.pdf
```

### 3. コミットメッセージ

```bash
git commit -m "Add daily slide for 2026-MM-DD: タイトル

- Convert PDF to images (N slides)
- Generate slide HTML with {theme} theme
- Update daily_slides_index.html with new entry

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## 🔍 参考リンク

- [GitHub Pages公式ドキュメント](https://docs.github.com/en/pages)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [.nojekyll について](https://github.blog/2009-12-29-bypassing-jekyll-on-github-pages/)
- [GitHub Actions - upload-pages-artifact](https://github.com/actions/upload-pages-artifact)

## 📝 変更履歴

### 2026-01-08
- **初版作成**: 3つの再利用可能スクリプトを作成
- **Jekyll無効化**: `.nojekyll` 追加、`pages.yml` 修正
- **JavaScript修正**: `index.html` の最新スライド取得ロジックを修正
- **01/08スライド**: ChatGPTヘルスケア（health theme）
- **01/07スライド**: NVIDIA Rubin（tech theme）

### トラブルシューティング実績
1. ✅ Jekyllキャッシュ問題 → `.nojekyll` で解決
2. ✅ Gitサブモジュールエラー → `.worktrees/` 削除
3. ✅ JavaScriptセレクタ問題 → `.slide-card` 構造に対応
4. ✅ 文字コードエラー → 絵文字削除
5. ✅ GitHub Pagesキャッシュ → HTMLコメント追加で強制更新

## 💡 今後の改善案

1. **ワンコマンド化**: 3つのスクリプトを1つにまとめる
   ```bash
   python scripts/generate_daily_slide.py 0109 "タイトル" "説明文"
   ```

2. **対話型スクリプト**: 引数なしで実行すると対話的に入力
   ```bash
   python scripts/generate_daily_slide.py
   # → 日付を入力してください (MMDD):
   # → タイトルを入力してください:
   ```

3. **自動コミット**: GitHub Actions で自動実行
   ```yaml
   on:
     push:
       paths:
         - 'input/day/*.pdf'
   ```

4. **テーマ設定ファイル**: YAMLで色を管理
   ```yaml
   themes:
     health:
       primary: "#10b981"
       accent: "#059669"
   ```
