# おすすめ便利ツールサイト自動更新スキル

## 概要

このスキルは、「仕事が速くなる おすすめ便利ツール」サイト（recommended_tools.html）のコンテンツを、AIを活用して自動的に最新化・改善するための機能を提供します。

## 使い方

### 基本コマンド

```
おすすめツールサイトを更新して
ツール価格情報を最新化して
新しいAIツールを追加して
```

### 詳細指定

```
ChatGPT Teamの価格を$30に更新して
Perplexity Proをツールリストに追加して
直近1ヶ月の注目AIツールを調査して反映して
```

## 実行される処理

### 1. 価格情報の自動更新

各ツールの公式サイトから最新価格を取得し、以下のセクションを更新：
- 目的別ガイドの価格表示
- チーム規模別おすすめセットの価格
- コスト計算機のデータ属性
- 稟議書テンプレートの価格情報

### 2. 新規ツール追加

新しいAIツールをサイトに追加：
- ツールカードHTMLの生成
- TOOL_METAへのメタデータ追加
- コスト計算機への選択肢追加
- 稟議書テンプレートへのデータ追加

### 3. 「直近1ヶ月の注目」セクション更新

主要AIニュースソースから最新情報を収集：
- 大型モデルリリース（GPT、Claude、Gemini等）
- 業務自動化ツールの新機能
- エンタープライズAIの動向

## 更新対象ファイル

```
presentations/
  └── recommended_tools.html    # メインHTMLファイル
```

### 更新箇所

| セクション | 行番号目安 | 内容 |
|-----------|-----------|------|
| 目的別ガイド | 1959-2133 | ツール価格・リンク |
| チーム規模別おすすめ | 2147-2224 | 価格・構成提案 |
| コスト計算機 | 2348-2416 | data-monthly/annual属性 |
| 稟議書テンプレート | 8073-8124 | toolDataオブジェクト |
| TOOL_META | 6554-6584 | ツールメタデータ |

## データソース

### 価格情報取得先

| ツール | 公式価格ページ |
|--------|---------------|
| ChatGPT | https://chatgpt.com/pricing |
| Claude | https://claude.ai/pricing |
| Notion | https://www.notion.com/pricing |
| Slack | https://slack.com/pricing |
| Perplexity | https://www.perplexity.ai/enterprise/pricing |
| Zapier | https://zapier.com/pricing |
| Granola | https://www.granola.ai/pricing |
| NotebookLM | https://one.google.com/about/google-ai-plans |

### AIニュースソース

- OpenAI Blog / Announcements
- Anthropic News
- Google AI Blog
- Microsoft AI Blog
- Product Hunt (AI Tools)
- TechCrunch (AI Section)

## 価格更新時の注意

1. **通貨統一**: USD建てを基本とし、日本円は155円/USDで換算
2. **日付記載**: 「2026年1月時点」等の日付を必ず更新
3. **プラン名確認**: Plus/Pro/Team/Business等のプラン名が正しいか確認
4. **年払い割引**: 年払い価格と月払い価格の両方を記載

## 出力例

### 価格更新ログ

```
=== おすすめツールサイト価格更新 ===
日時: 2026-01-17

[更新済み]
- ChatGPT Team: $25-30/月（変更なし）
- Claude Pro: $20/月 → $22/月（値上げ）
- Notion Business: $20/月（変更なし）

[確認必要]
- Perplexity Pro: 価格ページ取得失敗

[新規追加検討]
- Grok 3 (xAI): $20/月 - 新規リリース
```

### 新規ツール追加テンプレート

```html
<div class="tool-card" id="tool-[ID]">
  <h3>[ツール名] <span class="badge">[カテゴリ]</span></h3>
  <p class="tool-subtitle">[サブタイトル]</p>
  <p class="tool-description">[説明文]</p>
  <div class="tool-section">
    <h4>主な特徴</h4>
    <ul>
      <li>[特徴1]</li>
      <li>[特徴2]</li>
    </ul>
  </div>
  <div class="tool-section">
    <h4>稟議ポイント</h4>
    <ul>
      <li>料金: [価格情報]</li>
      <li>セキュリティ: [セキュリティ情報]</li>
    </ul>
  </div>
  <div class="tool-section">
    <h4>リンク</h4>
    <ul>
      <li><a href="[公式URL]" target="_blank" rel="noopener">公式サイト</a></li>
    </ul>
  </div>
</div>
```

## トラブルシューティング

### 価格取得に失敗する
→ WebFetchツールでURLアクセスを確認、robots.txtやCAPTCHAの制限を確認

### HTMLの構造が崩れる
→ 更新前にバックアップを取り、差分を確認してから反映

### コスト計算機が動作しない
→ data-monthly/data-annual属性が正しい数値形式か確認

## 自動更新スケジュール（推奨）

| 頻度 | 対象 | 内容 |
|------|------|------|
| 週次 | 価格情報 | 主要ツールの価格変更確認 |
| 月次 | 新規ツール | Product Hunt等から注目ツール追加 |
| 四半期 | 全体レビュー | カテゴリ構成・導入効果目安の見直し |

## 関連ファイル

- [recommended_tools.html](../../../presentations/recommended_tools.html) - メインHTMLファイル
- [producthunt-tools-updater](../producthunt-tools-updater.md) - Product Huntからの新規ツール追加スキル

## 変更履歴

- 2026-01-17: 初版作成、価格情報を2026年1月時点に更新
