# Skill: デイリーAIニューススライド生成 (Daily AI News Slide Generation)

このスキルは、特定の日のAIニュース情報（テキストおよびPDF）を基に、ウェブサイト用のスライドHTMLを生成し、インデックスを更新してGitに成果物を反映させるための標準的なワークフローを定義します。

## 概要
1. **成果物**: 
   - スライド画像群 (`input/day/MMDD_slides/`)
   - スライドHTML (`presentations/day_slides/day_slide_YYYY_MM_DD.html`)
   - 更新されたインデックス (`presentations/day_slides_index.html`)

2. **入力ファイル**:
   - `input/day/MMDD.txt`: ニュースの要約テキスト
   - `input/day/MMDD-Topic.pdf`: 技術解説等の元PDF

## 手順

### 1. スクリプトの新規作成
前日のスクリプトをコピーして、該当日の日付（MMDD, YYYY_MM_DD）およびタイトル、内容を更新します。
- `convert_MMDD.py`: PDFから画像への変換用
- `create_slide_MMDD.py`: スライドHTML生成用
- `update_indexes_MMDD.py`: インデックス更新用

### 2. PDFの画像変換
`convert_MMDD.py` を実行し、PDFの全ページを画像に変換します。
```bash
python convert_MMDD.py
```
※ 完了後、生成された画像枚数を確認してください。

### 3. スライドHTMLの生成
`create_slide_MMDD.py` を実行します。
```bash
python create_slide_MMDD.py
```
- **注意**: 画像枚数が前の日と異なる場合は、スクリプト内のループ範囲（`range(1, N+1)`）を適切に修正してください。

### 4. インデックスの更新
`update_indexes_MMDD.py` を実行し、ポータルページのリストに新しいスライドへのリンクを追加します。
```bash
python update_indexes_MMDD.py
```

### 5. Gitへの反映
成果物および作成したスクリプトをGitにコミット・プッシュします。
```bash
git add .
git commit -m "Add daily slide for YYYY-MM-DD: [Topic]"
git pull --rebase
git push
```

## 注意点
- **デザインの一貫性**: `base_template.html` を使用し、トピックに合わせた配色（`--primary` 等のCSS変数）を設定してください。
- **セキュリティ**: Scriptsを実行する際は、内容を確認し、意図しない挙動がないか確認してください。
- **競合回避**: プッシュ前に必ず `git pull --rebase` を行い、リモートの変更を取り込んでください。
