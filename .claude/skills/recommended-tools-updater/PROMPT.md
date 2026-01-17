# おすすめツールサイト自動更新プロンプト

このプロンプトは、「仕事が速くなる おすすめ便利ツール」サイトのコンテンツを自動更新する際に使用します。

## 実行条件

以下のコマンドで起動:
- `おすすめツールサイトを更新して`
- `ツール価格を最新化して`
- `recommended_tools.htmlを更新して`

## 処理フロー

### 1. 価格情報の最新化

```
1. WebSearch で各ツールの最新価格を検索
   - クエリ例: "[ツール名] pricing 2026"

2. 検索結果から価格情報を抽出
   - 月額/年額
   - ユーザー単位/アカウント単位
   - 主要プラン（Plus/Pro/Team/Business/Enterprise）

3. recommended_tools.html の以下を更新:
   a. 目的別ガイド（purpose-cards セクション）の価格バッジ
   b. チーム規模別おすすめ（team-content セクション）の価格タグ
   c. コスト計算機（tool-checkboxes）の data-monthly/data-annual 属性
   d. 稟議書テンプレート（toolData オブジェクト）の価格情報
   e. 注意書きの日付（「2026年1月時点」等）
```

### 2. 新規ツール追加

```
1. 追加対象ツールの情報を収集:
   - 公式サイト URL
   - 価格プラン
   - 主な機能・特徴
   - セキュリティ情報（SOC2, GDPR等）
   - 対象ユーザー（個人/チーム/企業）

2. 適切なカテゴリセクションを特定:
   - AI系: AIモデル/チャット
   - 会議系: 議事録/会議効率化
   - コラボ系: ドキュメント/ナレッジ
   - 開発系: 開発ツール/SRE
   - 自動化系: ワークフロー/オートメーション

3. ツールカードHTMLを生成して追加

4. 必要に応じて以下も更新:
   - TOOL_META オブジェクト
   - コスト計算機の選択肢
   - 稟議書テンプレートの toolData
```

### 3. 「直近1ヶ月の注目」更新

```
1. 主要 AI ニュースサイトから最新情報を収集:
   - OpenAI Blog
   - Anthropic News
   - Google AI Blog
   - Product Hunt (AI カテゴリ)

2. 業務インパクトの大きいリリースを特定:
   - 大型モデルアップデート
   - 新機能リリース
   - 価格改定
   - エンタープライズ向け新サービス

3. サイトの「最新ニュース」セクションを更新
```

## 価格データ参照先

| ツール | 公式価格ページ | 価格帯 (USD/月) |
|--------|---------------|----------------|
| ChatGPT Plus | chatgpt.com/pricing | $20 |
| ChatGPT Team | chatgpt.com/pricing | $25-30 |
| Claude Pro | claude.ai/pricing | $20 |
| Notion Plus | notion.com/pricing | $10-12 |
| Notion Business | notion.com/pricing | $20-24 |
| Slack Pro | slack.com/pricing | $7.25-8.75 |
| Perplexity Pro | perplexity.ai/enterprise/pricing | $20 |
| Zapier Pro | zapier.com/pricing | $29.99 |
| Granola | granola.ai/pricing | $14-18 |
| NotebookLM Plus | one.google.com | $19.99 |
| Cursor Pro | cursor.sh/pricing | $16-20 |
| GitHub Copilot | github.com/features/copilot | $19 |

## 更新時の注意事項

1. **通貨**: USD 建てを基本とし、日本円換算は概算で付記
2. **日付**: 更新時に「YYYY年M月時点」を必ず更新
3. **プラン名**: 公式サイトのプラン名と一致させる
4. **ソース**: 可能な限り公式サイトの情報を使用
5. **バックアップ**: 大きな変更前は Git コミットを推奨

## 出力形式

更新完了後、以下の形式でレポートを出力:

```
=== おすすめツールサイト更新完了 ===
日時: YYYY-MM-DD HH:MM

【価格更新】
- ChatGPT Team: $25-30/月（変更なし）
- Claude Pro: $20/月（変更なし）
...

【新規追加】
- [ツール名]: [カテゴリ]に追加

【注意事項】
- [手動確認が必要な項目]

【次のアクション】
- git add presentations/recommended_tools.html
- git commit -m "update: recommended tools prices (YYYY-MM)"
- git push
```

## エラー対応

### 価格情報が取得できない場合
→ 「要確認」としてマーク、手動更新を促す

### HTMLの構造エラー
→ 更新をロールバック、差分を確認

### 外部サイトへのアクセス制限
→ キャッシュされた情報を使用、日付を明記
