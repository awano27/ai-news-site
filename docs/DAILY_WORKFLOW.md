# 日次作業・スライド修正ワークフロー

このドキュメントでは、日次のAIニューススライドの手動修正や素材準備に関する手順をまとめます。

## 1. PDF資料の画像変換 (convert_pdf_images.py)

PDF形式の資料（スライドなど）を、Webスライド用のJPEG画像に一括変換するツールの使い方です。

### 準備
`convert_pdf_images.py` をエディタで開き、以下の変数を処理対象に合わせて書き換えます。

```python
if __name__ == "__main__":
    # 変換したいPDFファイルのパス
    pdf_path = r"path/to/your/file.pdf"
    
    # 画像の出力先フォルダ
    output_dir = r"path/to/output/folder"
```

### 実行
ターミナルで以下のコマンドを実行します。

```bash
python convert_pdf_images.py
```

- 指定したフォルダに `slide_001.jpg`, `slide_002.jpg` ... の形式で保存されます。
- 画質はWeb用に調整されています（scale=2, JPEG quality=90）。

---

## 2. スライドのデザイン修正 (HTML/CSS)

2025/11/24の修正で導入された、リッチなコンテンツ表示用のCSSクラスとHTML構造です。`presentations/day_slides/` 配下のHTMLを編集する際に使用します。

### 主なコンポーネント

#### ハイライトボックス (重要事項の強調)
背景色付きの枠で囲み、左側にアクセントラインを表示します。

```html
<div class="highlight-box">
  ここに強調したいテキストや重要なポイントを記述します。
</div>
```

#### カード (情報のグループ化)
影付きの白いボックスで情報を囲みます。`accent` クラスを追加すると上部に色付きのラインが入ります。

```html
<div class="card accent">
  <h4>タイトル</h4>
  <p>説明文...</p>
</div>
```

#### 特徴グリッド (3カラムレイアウト)
アイコン付きの3列レイアウトで特徴などを並べて表示します。

```html
<div class="feature-grid">
  <!-- アイテム 1 -->
  <div class="feature-item">
      <span class="feature-icon">🧠</span>
      <div class="feature-title">推論モデル</div>
      <div class="feature-desc">
          説明文をここに記述します。
      </div>
  </div>
  <!-- アイテム 2, 3... -->
</div>
```

#### 見出し (h3)
左側にアクセントカラーのバーが付いたデザインの見出しです。

```html
<h3>見出しテキスト</h3>
```

---

## 3. 変更の反映 (Git操作)

作業が完了したら、変更をリポジトリに反映します。

1. **ステータスの確認**
   ```bash
   git status
   ```

2. **変更のステージング**
   ```bash
   git add <ファイルパス>
   # 例: git add presentations/day_slides/day_slide_2025_11_24.html
   ```

3. **コミット**
   変更内容を簡潔に記述します。
   ```bash
   git commit -m "Update 11/24 slide content and styles"
   ```

4. **プッシュ**
   ```bash
   git push
   ```
