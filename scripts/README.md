# Daily AI News JSON Generator

`input/day/` 配下のテキストファイルを読み込み、JSON API形式で出力するスクリプトです。

## 使い方

### 手動実行

```bash
node scripts/generate-daily-news-json.js
```

### 自動実行

GitHub Actionsで以下のタイミングで自動実行されます:

- **毎日 9:00 (JST)** - 定期実行
- **`input/day/*.txt` が更新されたとき** - プッシュトリガー
- **手動実行** - GitHub Actions の「Run workflow」から

## 出力ファイル

### 1. `presentations/api/daily-news.json`
全ニュースデータ (現在67件)

### 2. `presentations/api/daily-news-latest.json`
最新10件のニュースデータ

## JSON構造

```json
{
  "generatedAt": "2025-11-15T12:43:05.225Z",
  "totalCount": 67,
  "latestCount": 10,
  "items": [
    {
      "date": "2025-11-15",
      "filename": "1115.txt",
      "title": "記事タイトル",
      "summary": "概要テキスト",
      "surprise": "サプライズ理由",
      "sources": [
        {
          "text": "リンクテキスト",
          "url": "https://example.com"
        }
      ],
      "engineerPoints": "エンジニア向けポイント",
      "businessPoints": "ビジネス向けポイント",
      "comparison": "他候補との比較",
      "rawContent": "元のテキストファイルの内容"
    }
  ]
}
```

## API エンドポイント

GitHub Pages で公開されたJSON:

- **全データ**: https://awano27.github.io/ai-news-site/presentations/api/daily-news.json
- **最新10件**: https://awano27.github.io/ai-news-site/presentations/api/daily-news-latest.json

## 使用例

### JavaScript / Fetch API

```javascript
// 最新10件を取得
fetch('https://awano27.github.io/ai-news-site/presentations/api/daily-news-latest.json')
  .then(response => response.json())
  .then(data => {
    console.log(`Total: ${data.totalCount}`);
    data.items.forEach(item => {
      console.log(`${item.date}: ${item.title}`);
    });
  });
```

### cURL

```bash
# 最新10件を取得
curl https://awano27.github.io/ai-news-site/presentations/api/daily-news-latest.json

# jqで整形
curl -s https://awano27.github.io/ai-news-site/presentations/api/daily-news-latest.json | jq '.items[0]'
```

### Python

```python
import requests

# 最新10件を取得
response = requests.get('https://awano27.github.io/ai-news-site/presentations/api/daily-news-latest.json')
data = response.json()

for item in data['items']:
    print(f"{item['date']}: {item['title']}")
```

## 技術仕様

### 日付フォーマット
- ファイル名: `MMDD.txt` (例: `1115.txt`)
- JSON内の日付: `YYYY-MM-DD` (例: `2025-11-15`)

### セクション解析
スクリプトは以下のセクションを自動抽出します:

- `タイトル` または `**タイトル**`
- `概要` または `**概要（3〜5行）**`
- `なぜサプライズか`
- `一次情報リンク`
- `エンジニア視点` (5-1セクション)
- `ビジネス視点` (5-2セクション)
- `他の有力候補との比較`

### リンク抽出
- Markdown形式: `[text](url)`
- プレーンURL: `https://...`

## トラブルシューティング

### 空ファイルのスキップ
空のテキストファイルは自動的にスキップされます:
```
⚠️  Skipped: 0807.txt (empty or invalid)
```

### タイトルが「タイトル不明」になる
テキストファイルに `**タイトル**` セクションがない場合、デフォルト値が使用されます。
ファイルの先頭に以下の形式でタイトルを追加してください:

```
1. **タイトル**
   記事タイトルをここに記載
```

## メンテナンス

### ファイルサイズの最適化
データ量が増えた場合は、`daily-news-latest.json` の件数を調整できます:

```javascript
// scripts/generate-daily-news-json.js
const latestData = {
  items: newsItems.slice(0, 20)  // 10 → 20 に変更
};
```

### 日付範囲の調整
年を跨ぐ場合は、ファイル名のパース処理を調整する必要があります。
