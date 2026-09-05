# Production publication

ユーザーが「見えるようにpushして」と依頼し、mainへの統合と本番反映を承認。

- 作業用branch: codex/visionhub-content-integrity-20260905
- 検証済みbase main: c33aafde
- 既存checkoutのdirtyは変更しない。今回のコード訂正に加え、実在する9/5のCrusoe記事だけを公開用データへ適用する。他記事・件数・日時を維持する。
- 40関連テストは最新main移植時にPASS。既存homepage testは未修正HEADでもheroIdentity不在を再現済み（push-baseline-test.txt）。
- 先行branchのMojibake Guard run 33945406030: 文字化けcheck SUCCESS。large-files FAILは新規branchのbefore SHA=全0をgit revisionに使用した既存workflowの問題。origin/main..HEADで同じサイズ検査をローカル実行しPASS。本番main更新では実在before SHAになる。
- 本書作成時点では本番push前。公開状態はmainのHEADとGitHub Pages実行結果で確認する。

公開直前検証: 関連6テストファイルをpytest実行し40 passed in 21.08s。公開用実データ141件中Crusoe1件だけ変更、他140件と上位metadata全一致を主担当でも確認。訂正前企業価値の残留なし、git diff --check PASS。main更新はfast-forwardのみ、forceなし。
