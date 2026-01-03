# ツール自動収集システム (Tool Auto-Ingest System)

## 概要

このシステムは、Product Hunt、Hacker News、GitHubから毎日自動でAI/生産性ツールを収集し、スコアリング・分類・重複排除を行って構造化データとして保存します。GitHub Actionsで自動実行され、手動レビューを経て公開する運用フローを実現します。

## 主要機能

- **自動収集**: 3つのソース（Product Hunt, Hacker News, GitHub）から毎日新しいツールを取得
- **重複排除**: URL正規化、ドメイン比較、名前のファジーマッチングで重複を自動検出
- **自動分類**: キーワード解析により8カテゴリ（meeting/docs/pm/automation/ai/dev/ph/other）に分類
- **スコアリング**: ソース順位、投票数、URL品質、説明充実度などから0-100点のスコアを算出
- **検証**: JSON Schema準拠、URL検証、重複ID検出などの自動バリデーション
- **バージョン管理**: 日次ファイル（`data/daily/YYYY-MM-DD.json`）と統合ファイル（`data/tools.json`）の両方を保持

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions (毎日23:00 UTC)                │
└────────────┬────────────────────────────────────────────────────┘
             │
             v
┌────────────────────────────────────────────────────────────────┐
│                        収集フェーズ                              │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ Product Hunt │   │ Hacker News  │   │   GitHub     │       │
│  │  GraphQL API │   │ Firebase API │   │  Search API  │       │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘       │
│         │                  │                   │                │
│         └──────────────────┴───────────────────┘                │
│                            │                                    │
│                   scripts/collectors/                           │
│              (BaseCollector派生クラス)                           │
│                                                                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                       処理フェーズ                               │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 重複排除 (Deduplication)                                     │
│     - URL正規化・ドメイン比較                                     │
│     - 名前のファジーマッチング (85%閾値)                           │
│                                                                  │
│  2. カテゴリ分類 (Categorization)                                 │
│     - キーワードベース分類                                        │
│     - トピック/説明文の解析                                       │
│                                                                  │
│  3. スコアリング (Scoring)                                        │
│     - ソース順位: 30点                                           │
│     - 投票数/スター数: 25点 (対数スケール)                        │
│     - 公式URL有無: 15点                                          │
│     - 説明充実度: 10点                                           │
│     - トピック多様性: 10点                                        │
│     - 優先カテゴリ: 10点                                         │
│                                                                  │
│  scripts/ingest.py                                              │
│                                                                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                       保存フェーズ                               │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────┐            │
│  │  data/tools.json    │  │ data/daily/YYYY-MM-  │            │
│  │  (全ツール統合)      │  │ DD.json (日次収集)    │            │
│  └─────────────────────┘  └──────────────────────┘            │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────┐            │
│  │  data/index.json    │  │ data/schema/tool.json│            │
│  │  (統計情報)          │  │ (JSONスキーマ)        │            │
│  └─────────────────────┘  └──────────────────────┘            │
│                                                                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                       検証フェーズ                               │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  scripts/validate.py                                            │
│  - JSON Schema準拠チェック                                       │
│  - 必須フィールド検証                                            │
│  - URL形式検証                                                  │
│  - 重複ID検出                                                   │
│  - カテゴリ妥当性確認                                            │
│                                                                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                      コミット・公開                              │
└────────────────────────────────────────────────────────────────┘
```

## セットアップ手順

### 1. ローカル環境構築

```bash
# リポジトリをクローン
git clone https://github.com/awano27/ai-news-site.git
cd ai-news-site

# Python 3.11以上を使用
python --version  # 3.11以上であることを確認

# 依存関係をインストール
pip install -r requirements-ingest.txt
```

### 2. API認証情報の取得

#### Product Hunt API Token

**必須** - Product Huntからツールを収集するために必要

1. [Product Hunt Developer](https://www.producthunt.com/v2/oauth/applications)にアクセス
2. 新しいアプリケーションを作成
3. "API v2"を選択
4. "Developer Token"を取得（個人利用の場合はこれで十分）
5. 環境変数 `PH_TOKEN` に設定

**重要な制限**:
- 無料プラン: 200リクエスト/日
- レート制限に注意（スクリプトは2秒間隔でリクエスト）

#### GitHub API Token

**任意** - 設定すると検索APIのレート制限が緩和される

1. [GitHub Personal Access Token](https://github.com/settings/tokens)にアクセス
2. "Generate new token (classic)"を選択
3. スコープは`public_repo`のみでOK
4. 環境変字 `GITHUB_TOKEN` に設定

**レート制限**:
- 認証なし: 10リクエスト/分
- 認証あり: 30リクエスト/分

#### Hacker News API

**認証不要** - Firebase APIは公開されており認証不要

### 3. 環境変数の設定

```bash
# Linux/Mac
export PH_TOKEN="your_product_hunt_token_here"
export GITHUB_TOKEN="your_github_token_here"  # オプション

# Windows PowerShell
$env:PH_TOKEN = "your_product_hunt_token_here"
$env:GITHUB_TOKEN = "your_github_token_here"  # オプション
```

## 収集ソースの説明

### Product Hunt

- **API**: GraphQL API v2
- **対象**: 指定日に投稿されたツール（投票順で最大50件）
- **取得データ**:
  - 名前、タグライン、説明文
  - 投票数、コメント数
  - トピック（自動分類に使用）
  - 公式サイトURL、Product HuntページURL
- **分類ロジック**: トピック名とカテゴリマッピング（`_categorize_from_topics`）
- **API仕様**: [Product Hunt API Docs](https://api.producthunt.com/v2/docs)

**収集コード**: `scripts/collectors/producthunt.py`

### Hacker News

- **API**: Firebase REST API
- **対象**: Show HN投稿（指定日分、スコア10以上、最大30件）
- **取得データ**:
  - タイトル（"Show HN:"プレフィックスを除去）
  - 投稿URL、スコア
  - HNディスカッションURL
- **分類ロジック**: タイトル・URLのキーワード解析（`_categorize_from_content`）
- **名前抽出**: タイトルから"Name - Description"パターンを解析
- **API仕様**: [Hacker News API](https://github.com/HackerNews/API)

**収集コード**: `scripts/collectors/hn.py`

### GitHub

- **API**: Search Repositories API
- **対象**: 指定日以降に作成されたリポジトリ（スター10以上、最大30件）
- **検索クエリ**: `created:>=YYYY-MM-DD stars:>=10 is:public (productivity OR automation OR ai OR llm OR devtools OR cli)`
- **取得データ**:
  - リポジトリ名、説明文
  - スター数
  - トピック（GitHub topics）
  - ホームページURL、GitHubリポジトリURL
- **名前整形**: ハイフン/アンダースコアをスペース化、頭字語を大文字化
- **分類ロジック**: 全て`dev`カテゴリを含む + キーワード解析
- **API仕様**: [GitHub REST API](https://docs.github.com/en/rest/search)

**収集コード**: `scripts/collectors/github.py`

## API利用規約への注意事項

### 遵守すべきポイント

1. **レート制限の尊重**
   - Product Hunt: 2秒/リクエスト
   - Hacker News: 0.5秒/リクエスト
   - GitHub: 6秒/リクエスト（認証なし）、2秒/リクエスト（認証あり）

2. **User-Agentの設定**
   - すべてのリクエストに`AI-News-Site-Bot/1.0 (https://awano27.github.io/ai-news-site/)`を付与
   - ボットであることを明示

3. **リトライ戦略**
   - BaseCollectorクラスで自動実装
   - 429/500/502/503/504エラー時に最大3回リトライ
   - バックオフ係数: 2.0（指数バックオフ）

4. **データ利用目的**
   - 非商用の情報収集・整理目的
   - 収集元URLを必ず保持
   - robots.txtを尊重（API経由のため通常は問題なし）

5. **禁止事項**
   - 大量のパラレルリクエスト
   - データの再販売
   - API keyの共有

## ローカル実行方法

### 基本的な実行

```bash
# 昨日分を収集（デフォルト）
python scripts/ingest.py

# 特定の日付を指定
python scripts/ingest.py --date 2026-01-01

# ドライラン（保存せずに結果確認）
python scripts/ingest.py --dry-run

# ドライランで日付指定
python scripts/ingest.py --date 2026-01-01 --dry-run
```

### ログレベルの調整

```bash
# DEBUGレベルで詳細ログ
LOG_LEVEL=DEBUG python scripts/ingest.py

# WARNINGレベルでエラーのみ
LOG_LEVEL=WARNING python scripts/ingest.py
```

### 検証の実行

```bash
# 標準検証
python scripts/validate.py

# 厳格検証（オプションフィールドも検証）
python scripts/validate.py --strict
```

### 出力ファイルの確認

```bash
# 日次ファイル
cat data/daily/2026-01-01.json | jq '.tools[] | {name, score, categories}'

# 統合ファイル
cat data/tools.json | jq '.tools[0:5] | .[] | {name, score, source}'

# 統計情報
cat data/index.json | jq '.'
```

## GitHub Actions設定手順

### 1. Secretsの設定

1. GitHubリポジトリの `Settings` → `Secrets and variables` → `Actions` に移動
2. "New repository secret"をクリック
3. 以下のSecretsを追加:

   | Name | Value | 必須 |
   |------|-------|------|
   | `PH_TOKEN` | Product Hunt Developer Token | はい |
   | `GITHUB_TOKEN` | (自動提供) | いいえ |

**注意**: `GITHUB_TOKEN`は自動的に提供されるため、手動設定は不要です。高いレート制限が必要な場合のみ、Personal Access Tokenを上書き設定してください。

### 2. ワークフローの確認

`.github/workflows/ingest.yml`が以下のように設定されています:

```yaml
# 毎日23:00 UTC (日本時間 翌08:00) に実行
schedule:
  - cron: '0 23 * * *'

# 手動実行も可能（日付指定、ドライラン可）
workflow_dispatch:
  inputs:
    date:
      description: 'Target date (YYYY-MM-DD)'
      required: false
    dry_run:
      description: 'Dry run'
      required: false
      default: false
```

### 3. 手動実行

1. GitHubリポジトリの `Actions` タブに移動
2. "Daily Tool Ingest"ワークフローを選択
3. "Run workflow"をクリック
4. オプション:
   - **Target date**: 収集対象日（空欄で昨日）
   - **Dry run**: チェックすると保存せずに結果確認のみ

### 4. 実行結果の確認

1. Actionsタブでワークフロー実行を選択
2. "Summary"セクションでツール数・ソース別統計を確認
3. ログで詳細を確認

## 運用フロー（1分レビュー手順）

### 毎日の運用サイクル

```
23:00 UTC: 自動収集実行
  ↓
08:00 JST: 収集完了（通常5分以内）
  ↓
[手動レビュー - 所要時間: 1分]
  ↓
公開準備完了
```

### 1分レビューの手順

#### ステップ1: 新規ツールの確認（30秒）

```bash
# 最新の日次ファイルを確認
cat data/daily/$(date -I).json | jq -r '.tools[] | "\(.score) - \(.name) (\(.source))"' | head -20

# または、スコア順でトップ10のみ
cat data/tools.json | jq -r '.tools[0:10] | .[] | "\(.score) - \(.name)"'
```

**確認ポイント**:
- スコア70以上 → 自動的に高品質（通常そのまま公開OK）
- スコア50-69 → 説明文とURLを軽くチェック
- スコア50未満 → 低品質の可能性（`published: false`のまま）

#### ステップ2: カテゴリの妥当性チェック（20秒）

```bash
# カテゴリ別集計
cat data/index.json | jq '.categories'
```

**確認ポイント**:
- `other`カテゴリが多すぎないか（10%以下が理想）
- 明らかに誤分類されているものがないか

#### ステップ3: 重複チェック（10秒）

```bash
# 名前の重複確認（自動で排除されているはずだが念のため）
cat data/tools.json | jq -r '.tools[].name' | sort | uniq -d
```

通常は何も出力されないはず。

### レビュー後のアクション

#### 承認する場合（高品質ツール）

```bash
# tools.jsonを編集して published: true に変更
# 例: jq使用
cat data/tools.json | jq '.tools[] | select(.name == "ツール名") | .published = true' > tmp.json
mv tmp.json data/tools.json

# Git commit
git add data/
git commit -m "chore(data): approve tools for $(date -I)"
git push
```

#### 却下する場合（低品質ツール）

`published: false`のまま放置（デフォルト）。後で手動で削除することも可能。

```bash
# 削除する場合
cat data/tools.json | jq '.tools[] | select(.id != "tool-id-to-remove")' > tmp.json
mv tmp.json data/tools.json
```

#### カテゴリを修正する場合

```bash
# カテゴリ修正スクリプト（既存のfix_tool_categories.pyを参考）
python fix_tool_categories.py --id "tool-id" --add-category "ai" --remove-category "other"
```

## トラブルシューティング

### 問題1: Product Huntから収集できない

**症状**:
```
WARNING:scripts.collectors.producthunt:PH_TOKEN not set, skipping Product Hunt collection
```

**原因**: `PH_TOKEN`環境変数が未設定

**解決策**:
```bash
export PH_TOKEN="your_token"
python scripts/ingest.py
```

GitHub Actionsの場合:
- Repository Secretsで`PH_TOKEN`が設定されているか確認
- トークンの有効期限を確認（Product Huntで再発行が必要な場合あり）

### 問題2: GitHubレート制限に引っかかる

**症状**:
```
WARNING:scripts.collectors.github:GitHub rate limit exceeded, skipping
```

**原因**: GitHubの検索APIレート制限（認証なし: 10req/min）

**解決策**:
```bash
# Personal Access Tokenを設定
export GITHUB_TOKEN="ghp_xxxxx"
python scripts/ingest.py
```

または、スクリプトの`REQUEST_DELAY`を増やす（`scripts/collectors/github.py`）:
```python
REQUEST_DELAY = 10.0  # 6.0から10.0に変更
```

### 問題3: 検証エラーが出る

**症状**:
```
ERROR:scripts.validate:Validation FAILED with 5 errors
```

**原因**: データ不整合（通常は発生しないが、手動編集後に起こる可能性）

**解決策**:
```bash
# エラー詳細を確認
python scripts/validate.py --strict

# よくあるエラー:
# 1. 無効なURL → links.officialを修正
# 2. 不正なカテゴリ → categoriesを修正
# 3. 重複ID → 片方のIDを変更
```

### 問題4: 重複ツールが収集される

**症状**: 同じツールが異なるIDで複数回収集される

**原因**: URL正規化の不一致、名前の表記ゆれ

**解決策**:
```bash
# 重複を手動で確認
cat data/tools.json | jq -r '.tools[] | "\(.links.official) - \(.name)"' | sort

# 重複を削除（一方を削除）
cat data/tools.json | jq '.tools |= map(select(.id != "duplicate-id"))' > tmp.json
mv tmp.json data/tools.json

# 次回以降の重複を防ぐため、normalize_domain関数を確認
# scripts/ingest.py の normalize_domain()
```

### 問題5: スコアが異常に低い/高い

**症状**: 明らかに品質の高いツールがスコア30、低品質ツールがスコア90など

**原因**: スコアリングロジックの調整不足

**解決策**:
`scripts/config.py`の`SCORING_WEIGHTS`を調整:

```python
SCORING_WEIGHTS = {
    "source_rank": 30,      # ソース順位の重み（上げると上位ツールが有利）
    "source_votes": 25,     # 投票数の重み（上げると人気ツールが有利）
    "has_official_url": 15, # 公式URL有無（上げるとGitHub以外のサイトを優遇）
    "has_description": 10,  # 説明文の充実度
    "topic_diversity": 10,  # トピック多様性
    "category_match": 10    # 優先カテゴリマッチ
}
```

### 問題6: GitHub Actionsでcommitが失敗

**症状**:
```
error: failed to push some refs to 'github.com:awano27/ai-news-site.git'
```

**原因**: ブランチ保護ルール、または競合

**解決策**:
1. ブランチ保護を確認（Settings → Branches）
2. mainブランチへのpushが許可されているか確認
3. 手動でpull → merge → push

```bash
git pull origin main --rebase
git push origin main
```

### 問題7: 日本語ツール名が文字化けする

**症状**: ツール名・説明文が正しく表示されない

**原因**: エンコーディング問題（UTF-8 BOMなど）

**解決策**:
```bash
# 既存の文字化け修正スクリプトを参考
python fix_mojibake.py

# JSONファイルが正しくUTF-8（BOM無し）か確認
file -bi data/tools.json
# 出力: application/json; charset=utf-8
```

## 設定ファイルリファレンス

### scripts/config.py

```python
# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DAILY_DIR = DATA_DIR / "daily"
TOOLS_FILE = DATA_DIR / "tools.json"
INDEX_FILE = DATA_DIR / "index.json"

# スコアリング重み
SCORING_WEIGHTS = {
    "source_rank": 30,
    "source_votes": 25,
    "has_official_url": 15,
    "has_description": 10,
    "topic_diversity": 10,
    "category_match": 10
}

# 優先カテゴリ（スコアボーナスあり）
PRIORITY_CATEGORIES = ["ai", "automation", "meeting", "docs"]

# 重複判定閾値
DEDUPE_NAME_THRESHOLD = 0.85  # 85%以上の名前類似度で重複とみなす

# カテゴリ分類キーワード
CATEGORY_KEYWORDS = {
    "meeting": ["meeting", "video", "conference", ...],
    "docs": ["document", "wiki", "notion", ...],
    "pm": ["project", "task", "kanban", ...],
    "automation": ["automation", "workflow", "zapier", ...],
    "ai": ["ai", "gpt", "llm", "claude", ...],
    "dev": ["developer", "code", "github", "api", ...]
}
```

### .github/workflows/ingest.yml

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # 毎日23:00 UTC
  workflow_dispatch:     # 手動実行可能

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
      - name: Setup Python 3.11
      - name: Install dependencies
      - name: Run ingest (with PH_TOKEN, GITHUB_TOKEN)
      - name: Run validation
      - name: Commit and push (if changes detected)
```

## データスキーマ

### Tool オブジェクト

詳細は`data/schema/tool.json`を参照。主要フィールド:

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | string | はい | slug形式の一意ID（例: `my-tool-name`） |
| `name` | string | はい | ツール名（最大100文字） |
| `tagline` | string | はい | 1行説明（最大200文字） |
| `description` | string | いいえ | 詳細説明（最大2000文字） |
| `categories` | array | はい | カテゴリ配列（meeting/docs/pm/automation/ai/dev/ph/other） |
| `links.official` | string | はい | 公式サイトURL |
| `links.producthunt` | string | いいえ | Product HuntページURL |
| `links.hn` | string | いいえ | Hacker NewsスレッドURL |
| `links.github` | string | いいえ | GitHubリポジトリURL |
| `first_seen_at` | string | はい | 初回収集日（YYYY-MM-DD） |
| `source` | string | はい | 収集元（producthunt/hn/github/manual/rss） |
| `source_rank` | integer | いいえ | 収集元での順位 |
| `source_votes` | integer | いいえ | 投票数/スター数 |
| `score` | number | いいえ | 総合スコア（0-100） |
| `published` | boolean | はい | 公開フラグ（デフォルト: false） |
| `topics` | array | いいえ | トピック/タグ配列 |
| `updated_at` | string | はい | 最終更新日時（ISO 8601） |

## 参考リンク

- [Product Hunt API Documentation](https://api.producthunt.com/v2/docs)
- [Hacker News API](https://github.com/HackerNews/API)
- [GitHub REST API - Search](https://docs.github.com/en/rest/search)
- [JSON Schema Specification](https://json-schema.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## ライセンスとクレジット

このシステムは、各API提供元の利用規約に従って運用してください:

- Product Hunt: [Terms of Use](https://www.producthunt.com/terms)
- Hacker News: [API Guidelines](https://github.com/HackerNews/API#usage)
- GitHub: [API Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)

収集データには必ず出典リンクを保持し、適切にクレジット表示を行ってください。
