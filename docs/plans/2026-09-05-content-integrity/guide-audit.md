# AIコーディングエージェント比較ガイド監査

確認日: 2026-09-05（Asia/Tokyo）
対象: `presentations/ai_coding_agents_guide.html`、関連する `presentations/copilot-guide/cli.html`

## 生成経路と公開版

- `rg` で `ai_coding_agents_guide` を検索した結果、対象HTML以外のテンプレート、入力データ、生成スクリプト、派生 JSON/RSS は見つからなかった。`git log --follow` も当該HTMLを直接更新した履歴を示す。このため、比較ガイドはこのリポジトリでは手動管理のHTMLとして扱い、新しい生成器は追加しない。
- 公開URL `https://visionhub.jp/presentations/ai_coding_agents_guide.html` は修正前に取得できた（HTTP取得 PASS）。公開版にもローカル修正前と同じ「Claude Code はサンドボックスなし」およびHooksの独自性断定があった。今回の作業はローカルファイルだけであり、本番には未反映。
- `presentations/copilot-guide/cli.html` は、同じ「承認と隔離の混同」が scoped 検索で見つかった関連ページである。`--allow-all` の説明を、承認範囲とsandbox設定を分ける文に訂正した。

## 主張別記録

|対象・修正前の主張|判定|根拠（節）|修正内容|
|---|---|---|---|
|比較表: Claude Code は「なし（ユーザー承認制で安全性を確保）」|誤り|[Claude Code sandboxing docs](https://code.claude.com/docs/en/sandboxing) の「Get started」「Sandbox modes」「How sandboxing works」。Bash sandbox は macOS/Linux/WSL2 で利用でき、Bashと子プロセスにOSレベルで境界を適用する。|任意有効化のBash sandbox、対応OS、ネイティブWindows未対応を記載。承認と隔離を別設定として説明した。|
|比較表: Claude Code は「ローカルで直接実行。ファイルシステムに完全アクセス」|情報が古い／条件不足|同 docs の「Filesystem isolation」「Disable filesystem isolation」。既定の書込み先は作業ディレクトリ、セッション一時ディレクトリ、追加許可ディレクトリ。読取り範囲・例外は設定依存。|「完全アクセス」を削除し、既定の読書込み範囲、許可ドメイン、deny設定を根拠注記に記載した。|
|「承認制で安全性を確保」|根拠の弱い断定|同 docs の「How sandboxing relates to permissions and permission modes」「The unsandboxed retry escape hatch」。権限フローとsandboxは別で、互換性などでは通常権限フローまたはsandbox外再試行がある。|安全を保証する表現を削除。`/sandbox`、`allowUnsandboxedCommands`、sandbox外実行の条件を記載した。|
|Claude Code Hooks は「唯一の自動介入システム」、Copilot等には「存在しない」|誤り|[GitHub Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/hooks) の「What are hooks」「Types of hooks」。Copilot CLI と Cloud Agent でHooksが使え、preToolUseで実行判断に介入できる。|唯一・不存在の断定を削除。Claude/Copilotともイベント、実行環境、設定範囲、失敗時の挙動を確認する比較へ変更。|
|Copilot Hooks をClaude Hooksと同一の条件で利用できるかの説明がない|情報が古い／条件不足|[GitHub Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference) の「Cloud agent execution environment」「preToolUse decision control」「Command vs HTTP fail behavior for preToolUse」。Cloud Agentは非対話でaskをdeny扱い、policy hooksはCLIのみ、command/HTTPで失敗時が異なる。|Copilot CLI/Cloud Agentを分離し、allow/deny/ask、Cloud Agentのask、policy hooks、hook種別の制限を明記した。|
|CodexのOS sandbox、他製品との安全性・GUI・並列性・設定形式の優劣|未確認（比較順位の根拠なし）|同一OS・クライアント・設定・許可パス・ネットワーク方針をそろえた比較根拠を本作業では確認できなかった。OpenAI開発者資料を検索したが、この表に載せるOS別の直接仕様を確定できなかった。|具体仕様と順位の断定を削除し、比較に必要な条件と公式資料確認を示した。未確認を「非対応」とはしていない。|
|特定モデルのベンチマークから製品全体の優劣を導く説明|根拠の弱い断定|同じモデル・版・プラン・ハーネス・実行設定をそろえた比較根拠がない。|性能順位の記述を削除し、モデル名、製品、実行面、評価条件を分ける注記へ変更した。|
|Antigravityの料金、無料モデル、並列数、提供形態、性能の断定|未確認|本作業の一次資料では直接確認できなかった。|具体値と比較順位を削除。将来掲載する場合の確認日、公式料金/モデル資料、正式提供/プレビュー、OS・有効化条件を示した。|
|Copilot CLI: `--allow-all` は「サンドボックスなしで全操作を自動承認」|誤り|[Allowing and denying tool use](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools) の「Permissive options」、[Using Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview) の「Use sandboxing」。`--allow-all`はtools/paths/URLsの承認であり、sandboxは別設定。|2箇所を訂正し、`/sandbox enable` と公式リンクを追加した。|

## 再発防止の境界

- `scripts/check_coding_guide_integrity.py` は、今回訂正した既知の誤り（Claude Code sandboxなし、承認を隔離の代替とする表現、Hooksの唯一性、他製品の不存在、根拠なしの安全性順位）と、根拠リンク・必須条件を **ERROR** にする。
- 「完全自動」「最適解」「完全アクセス」は、使われた場合に適用条件を人が確認すべき **WARNING** とする。これは外部事実や製品品質を自動で保証する検査ではない。
- 公式ページを取得できないことを非対応の根拠にはしない。今回のCodex/Antigravityのように直接仕様を確定できない項目は未確認として中立化した。

主担当追記: Hooks公式設定場所表とPreToolUse節、Copilot Hooks locations/Cloud agent execution environmentを本文確認し設定パスとCloud制限を追記。比較表の完全自律・Review→Merge全自動、価格階層不存在も未確認として中立化。限定訂正履歴を表示。ブラウザー確認実施済み、詳細はREPORT.md。
