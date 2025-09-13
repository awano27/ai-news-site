# AIニュースアーカイブシステム

このシステムは、inputディレクトリからAIニュースデータを自動的に抽出してアーカイブを構築します。

## 📁 システム構成

```
ai-news-site/
├── input/day/               # 日別ニュースファイル（*.txt）
├── public-pages/news/       # 生成されたアーカイブデータ
│   ├── archive_index.json   # アーカイブインデックス
│   ├── version.json         # バージョン管理
│   └── YYYY-MM-DD.json      # 日別ニュースデータ
├── presentations/
│   └── news_archive.html    # アーカイブビューアー
└── update_news_archive.py   # アーカイブ更新スクリプト
```

## 🚀 クイックスタート

### 1. 新しいニュースを追加
```bash
# 1. input/day/ディレクトリに新しいテキストファイルを追加
# ファイル名形式: MMDD.txt (例: 0913.txt = 9月13日)

# 2. アーカイブを更新
python update_news_archive.py

# 3. 変更をコミット・プッシュ
git add public-pages/news/
git commit -m "add: latest AI news archive"
git push origin main
```

### 2. アーカイブを確認
- **オンライン**: https://awano27.github.io/ai-news-site/presentations/news_archive.html
- **ローカル**: `presentations/news_archive.html`をブラウザで開く

## 📄 ニュースファイル形式

### input/day/MMDD.txt の形式
```
ニュースタイトル（1行目）
主な内容の説明...

主要発表: 詳細情報...
技術の概要: 技術的な説明...
・ポイント1
・ポイント2
■ 重要な情報

URL関連情報:
公式サイト: https://example.com
発表記事: https://example.com/news
```

### 生成されるJSON形式
```json
{
  "date": "2025-09-13",
  "source": "input/day/0913.txt",
  "count": 1,
  "items": [
    {
      "title": "ニュースタイトル",
      "score": 85,
      "rank": 1,
      "url": "https://example.com",
      "summary": "要約テキスト...",
      "points": ["・ポイント1", "・ポイント2"],
      "links": [{"href": "URL", "text": "リンク名"}],
      "category": "AI Model",
      "date": "2025-09-13"
    }
  ]
}
```

## ⚙️ 自動化機能

### スコア計算
- タイトルの長さ
- 要約の質
- URL数
- 重要キーワードの存在
- **スコア範囲**: 20-100

### カテゴリ自動分類
- **AI Model**: GPT, LLM, Transformer, Neural関連
- **Business**: 資金調達, 投資, IPO, 買収関連
- **Research**: 論文, 研究, 実験, テスト関連
- **Product**: リリース, 発表, ローンチ関連
- **Hardware**: チップ, GPU, CPU, ハードウェア関連

### ポイント抽出
自動的に重要なポイントを抽出:
- 箇条書き（・, -, •, ★, ■）
- 番号付きリスト（1., 2., 3...）
- 重要キーワード含有行（発表, 革命, リリース, ブレークスルー等）

## 🔧 高度な設定

### 強制更新
今日のデータは常に最新に更新されます。過去のデータを強制更新する場合:

```python
# update_news_archive.py の should_update ロジックを変更
should_update = True  # 強制更新
```

### カスタムカテゴリ
新しいカテゴリを追加する場合、`extract_news_content` 関数の `tech_keywords` を編集:

```python
tech_keywords = {
    "AI Model": ["GPT", "LLM", "Transformer"],
    "New Category": ["keyword1", "keyword2"]  # 追加
}
```

### URL抽出の改善
URLが正しく抽出されない場合、正規表現パターンを調整:

```python
url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
```

## 🌐 アーカイブビューアー機能

### news_archive.html の機能
- **日付フィルター**: 特定の日付のニュースを表示
- **キーワード検索**: タイトル・要約内のテキスト検索
- **全期間表示**: すべてのニュースを時系列で表示
- **レスポンシブデザイン**: モバイル対応
- **リアルタイム更新**: キャッシュ無効化で最新データを取得

### 利用可能な操作
1. **日付選択**: ドロップダウンから特定日を選択
2. **検索**: キーワード入力でリアルタイム絞り込み
3. **詳細表示**: 各ニュースの詳細ページへリンク
4. **外部リンク**: 元記事へのアクセス

## 📊 統計情報

### 現在のアーカイブ状況
- **総エントリ数**: 41件
- **日付範囲**: 2025年7月30日 ～ 2025年9月13日
- **データソース**: input/day/*.txt
- **最終更新**: 自動（version.jsonで追跡）

### パフォーマンス
- **アーカイブ生成時間**: ~5秒（41ファイル）
- **キャッシュ**: ブラウザキャッシュ + バージョンハッシュ
- **ファイルサイズ**: 平均2-5KB/ニュース

## 🔧 トラブルシューティング

### 一般的な問題

#### 1. アーカイブが更新されない
```bash
# キャッシュクリア
rm public-pages/news/version.json

# 強制更新
python update_news_archive.py
```

#### 2. 文字化け
- `input/day/*.txt` ファイルがUTF-8エンコーディングになっているか確認
- Windowsの場合、BOMなしUTF-8を使用

#### 3. URLが抽出されない
- URLが正しい形式（http://またはhttps://）になっているか確認
- スペースや改行でURLが分割されていないか確認

#### 4. カテゴリが正しく分類されない
- キーワードを追加または調整
- 大文字小文字の区別なし

### ログ出力
```bash
python update_news_archive.py
# 出力例:
# Updated: 2025-09-13 (0913.txt)
# Update completed:
# - Processed files: 1
# - Total entries: 41
# - Latest date: 2025-09-13
```

## 🔄 定期メンテナンス

### 週次タスク
1. 新しいニュースファイルの追加確認
2. アーカイブの動作確認
3. エラーログの確認

### 月次タスク
1. 古いデータの品質チェック
2. カテゴリ分類の精度確認
3. ディスク容量の確認

## 🚀 今後の改善予定

### 予定機能
- [ ] RSS フィード生成
- [ ] API エンドポイント追加
- [ ] 画像・動画の自動抽出
- [ ] 感情分析スコア
- [ ] トレンド分析ダッシュボード

### 技術改善
- [ ] マルチスレッド処理での高速化
- [ ] より精密なNLP処理
- [ ] 機械学習ベースのカテゴリ分類
- [ ] 自動要約生成

---

## 📞 サポート

問題や改善提案がある場合は、GitHubのIssueで報告してください。

**最終更新**: 2025年9月13日