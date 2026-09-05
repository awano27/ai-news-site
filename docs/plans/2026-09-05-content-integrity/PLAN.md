# VisionHub content integrity PLAN
確認日: 2026-09-05 Asia/Tokyo
## Goal and scope
比較ガイドのsandbox/hooks/優劣表現と9月5日Crusoe記事を一次資料と照合し、ローカル修正、再生成、回帰検証、監査記録まで完了する。CNAME=visionhub.jp、origin=awano27/ai-news-siteを確認。追加AGENTS.mdは検索で見つからず、ユーザー提供指示を適用。
## Work and dependencies
1. 既存dirtyを保全。ルートPLAN.mdは既存編集済みのため本ファイルに計画を分離。
2. Terra担当: 比較ガイドの現在/公開本文と公式資料を照合し、該当HTML・専用テスト・claim監査を修正。生成経路も確認。
3. Terra担当: Daily Newsデータ経路とCrusoeの原文照合、最初の不一致、訂正手段・公開前検査・固定fixture回帰テストを実装。担当2と独立。
4. 主担当: 公開URLと派生出力確認、両担当レビュー、ローカル生成・表示・関連テスト、監査報告統合。
## Constraints and risks
本番deploy/push/merge/commit禁止。秘密情報/環境変数操作禁止。有料APIなし。既存dirtyに触る必要があれば現状保存の上最小差分。過去一括再生成禁止。未確認を不存在/誤りと推定しない。全文転載禁止。
## Acceptance
公式本文に直接根拠と条件を付ける。承認とOS sandboxと実行面を分離。数値はcurrency/metric/event/timeで照合しmillion/billion/万/億換算を固定fixtureで検査。同指標矛盾検出と別指標非誤検出。修正前FAIL/後PASSを可能な範囲で保存。一時出力から再生成し二重実行で訂正重複なし。関係するHTML/JSON/RSSを照合。表示/リンク本文/差分をレビューし実行コマンドとPASS/FAIL/BLOCKED/NOT_RUNを記録。
## Review
担当出力は主担当が根拠、範囲、境界条件、互換性、保守性を確認して受け入れる。未確認と未実行を明示し本番未反映で終了。

## Push follow-up
ユーザーのpush指示により、最新origin/main c33aafdeを基点にcodex/visionhub-content-integrity-20260905へ今回差分だけを移植。8既存ファイルの3-way適用は競合なし。元checkoutのdirtyとローカル固有コミットは含めない。専用worktreeで関連tests/checker/diffを再検証し、今回ファイルだけcommit/push。main merge/deployは行わない。初回監査は旧checkoutでの実行記録として保持する。

## Production follow-up
ユーザーが本番に見えるようmainへpushすることを明示承認。最新mainとの差分は今回1コミットのみ。Terraは9/5の実在141件データ内のCrusoeと実在派生出力だけを訂正し無関係記事/日付/件数を保持。主担当はchecker/関連検査/生成差分を確認しmainへfast-forward push、GitHub Pages成功と公開本文・訂正JSONを確認する。既存dirty checkoutは触らず、全アーカイブ生成/有料APIは実行しない。既存homepage test失敗は前ターンでbaseline再現済み、同条件なら再実行不要。
