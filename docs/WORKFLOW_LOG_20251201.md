# 2025/12/01 AIニュースサイト更新手順ログ

本日実施した作業の手順まとめです。次回以降の参考にしてください。

## 1. 準備 (Input)
以下のファイルを `input/day/` ディレクトリに配置・更新しました。
- **原稿テキスト**: `input/day/1201.txt` (記事のタイトル、要約、本文など)
- **トップ画像**: `input/day/1201.png` (スライドのヘッダー画像)
- **元スライドPDF**: `input/day/1201-Bridging_the_AI_Divide.pdf` (配布用兼画像変換元)

## 2. スライドページの作成 (HTML)
1. **ベース作成**: 前日分 (`presentations/day_slides/day_slide_2025_11_30.html`) をコピーして、当日のファイル `presentations/day_slides/day_slide_2025_12_01.html` を作成。
2. **内容更新**: `1201.txt` の内容に基づき、タイトル、日付、ハイライト、詳細セクションを書き換え。

## 3. スライド画像の生成と埋め込み
PDFをWebページ上で閲覧できるように画像化しました。

1. **画像変換**: Pythonスクリプト（`convert_pdf_images.py` または一時スクリプト）を使用。
   ```python
   # 実行例
   pdf_path = "input/day/1201-Bridging_the_AI_Divide.pdf"
   output_dir = "input/day/1201_slides"
   # PDFの各ページを slide_001.jpg, slide_002.jpg... として出力
   ```
2. **HTML埋め込み**: 生成した画像フォルダ (`input/day/1201_slides/`) 内の画像を `day_slide_2025_12_01.html` に `<img>` タグで縦に並べて配置。
   ```html
   <div class="slides-container">
       <img src="../../input/day/1201_slides/slide_001.jpg" ...>
       <img src="../../input/day/1201_slides/slide_002.jpg" ...>
       ...
   </div>
   ```

## 4. リンクの更新
サイト内の導線を最新版に更新しました。

1. **スライド一覧**: `presentations/day_slides_index.html` のリスト最上部に、新しいスライドへのリンクを追加。
2. **トップページ**: `index.html` のヒーローセクションにある「今日のスライドを見る」ボタンのリンク先 (`href`) を `presentations/day_slides/day_slide_2025_12_01.html` に変更。

## 5. 公開 (Git Deployment)
GitHub Pagesへの反映を行いました。

1. **ファイル追加**: 作成・変更したファイルだけでなく、**新しい画像(png/jpg)やPDF**も忘れずにステージング。
   ```bash
   git add presentations/day_slides/day_slide_2025_12_01.html
   git add presentations/day_slides_index.html
   git add index.html
   git add input/day/1201.txt
   git add input/day/1201.png
   git add input/day/1201-Bridging_the_AI_Divide.pdf
   git add input/day/1201_slides/
   ```
2. **コミット & プッシュ**:
   ```bash
   git commit -m "Update slides for 2025-12-01"
   git push origin main
   ```
   ※ リモート側で変更がある場合は `git pull` してマージしてからプッシュ。
