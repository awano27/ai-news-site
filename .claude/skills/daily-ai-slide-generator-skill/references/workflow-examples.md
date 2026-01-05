# ワークフロー実行例

## 実際の実行ログ（2026-01-05の例）

### ステップ1: PDF画像変換

```bash
python convert_0105.py
```

出力:
```
Found PDF: input/day\0105-Sentient Sparks Program Guide.pdf
Converting input/day\0105-Sentient Sparks Program Guide.pdf to images...
Total pages: 13
Saved input/day/0105_slides\slide_001.jpg
Saved input/day/0105_slides\slide_002.jpg
...
Saved input/day/0105_slides\slide_013.jpg
Conversion complete!
```

### ステップ2: スライドHTML生成

```bash
python create_slide_0105.py
```

出力:
```
Generated presentations/day_slides/day_slide_2026_01_05.html
```

生成されたHTMLの特徴:
- テーマ: AGI/コミュニティ（紫×ティール）
- スライド枚数: 13ページ
- レスポンシブデザイン対応
- TOPに戻るボタン付き

### ステップ3: インデックス更新

自動的に `presentations/day_slides_index.html` に以下のエントリを追加:

```html
<li>
    <a href="day_slides/day_slide_2026_01_05.html" class="slide-link">
        <span class="date">2026/01/05</span>
        <span class="slide-title">Sentient Sparks: オープンソースAGIコミュニティプログラム</span>
    </a>
</li>
```

### ステップ4: Git操作

```bash
git add convert_0105.py create_slide_0105.py \
  "input/day/0105-Sentient Sparks Program Guide.pdf" \
  input/day/0105.png input/day/0105.txt \
  input/day/0105_slides/ \
  presentations/day_slides/day_slide_2026_01_05.html \
  presentations/day_slides_index.html

git commit -m "Add daily slide for 2026-01-05: Sentient Sparks Program

- Convert PDF to images (13 slides)
- Generate slide HTML with AGI community theme
- Update day_slides_index.html with new entry
- Clean up git conflict markers in index

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git pull --rebase
git push
```

出力:
```
[main d9ae789] Add daily slide for 2026-01-05: Sentient Sparks Program
 20 files changed, 715 insertions(+), 5 deletions(-)
 create mode 100644 convert_0105.py
 create mode 100644 create_slide_0105.py
 ...
Successfully rebased and updated refs/heads/main.
To https://github.com/awano27/ai-news-site.git
   af784cc..d9ae789  main -> main
```

## パフォーマンス

- **PDF変換**: 約10秒（13ページ）
- **HTML生成**: 約1秒
- **Git操作**: 約5-10秒（ネットワーク速度依存）
- **合計**: 約15-20秒

## 生成されたファイル一覧

```
D:\ai-news-site-main\
├── convert_0105.py                                    # 新規作成
├── create_slide_0105.py                               # 新規作成
├── input/day/
│   ├── 0105-Sentient Sparks Program Guide.pdf        # 入力
│   ├── 0105.png                                       # 入力
│   ├── 0105.txt                                       # 入力
│   └── 0105_slides/                                   # 新規作成
│       ├── slide_001.jpg
│       ├── slide_002.jpg
│       ├── ...
│       └── slide_013.jpg
└── presentations/day_slides/
    ├── day_slide_2026_01_05.html                     # 新規作成
    └── day_slides_index.html                         # 更新
```

## エラーハンドリング

### ケース1: PDFファイルが見つからない

```python
Error: No PDF file found for 0105 in input/day/
```

**解決策**: `input/day/` に `0105-*.pdf` 形式のファイルを配置

### ケース2: Git コンフリクト

```
CONFLICT (content): Merge conflict in presentations/day_slides_index.html
```

**自動解決**:
1. コンフリクトマーカー `<<<<<<< HEAD` を検出
2. 両方の変更をマージして日付順に整列
3. `git add` でマークして `git rebase --continue`

### ケース3: テンプレートファイルが見つからない

```python
Template not found: base_template.html
```

**解決策**: プロジェクトルートに `base_template.html` を配置

## カスタマイズ例

### 異なるテーマカラーを使用

```python
# create_slide_0105.py を編集
css_vars = """
:root {
  --primary: #dc2626;      # 赤系テーマ
  --accent: #f59e0b;       # オレンジアクセント
  --bg-light: #fef2f2;
  --bg-dark: #7f1d1d;
}
"""
```

### スライドレイアウトの変更

```python
# intro_box の内容をカスタマイズ
intro_box = """
<div style="...">
    <p>カスタムメッセージ</p>
</div>
"""
```

## 次のステップ

1. 生成されたスライドをブラウザで確認
2. 必要に応じてCSSをカスタマイズ
3. GitHub Pages で公開を確認

公開URL:
```
https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2026_01_05.html
```
