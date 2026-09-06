# 根拠レコードを手元で再現する

[設計記事](../../articles/claim-evidence-design.html)のサンプル。公開コード
`0b9ad2b115fdcb83291cf7f3f928ff7edba1a708` の `validate_bundle`、
`render_evidence`、`render_static_page`、`check_static_page` を直接呼ぶ。
別の検証器・レンダラーは作らない。データはすべて架空である。

## 確認した環境と依存関係

2026-09-05、Windows（OS build 26200）、PowerShell 7.6.5、Python 3.11.15、
Git 2.55.0.windows.2 で、以下の新規クリーンチェックアウト手順と実行を確認した。
Python標準ライブラリだけを使用し、pip install、Node、pytest、APIキー、有料APIは不要。
Linux/macOSでは未実行。PythonとGitのインストール自体は今回の検証対象外。

## 準備（Git取得は通信する）

まず固定版のサンプル本体とフィクスチャを、新しいディレクトリへ取得する。
以下はPowerShellで実行する。サンプル版は `3d5b903b06dca4bf92e951c5ba6cd5b486de25ab`。
このREADMEは記事の配信版に含まれ、実行コードとデータをこの先行コミットへ固定する。

```powershell
New-Item -ItemType Directory -Path sample-download | Out-Null
$sampleBase = 'https://raw.githubusercontent.com/awano27/ai-news-site/3d5b903b06dca4bf92e951c5ba6cd5b486de25ab/examples/claim-evidence'
foreach ($name in @('fixtures.json', 'reproduce.py')) {
    Invoke-WebRequest "$sampleBase/$name" -OutFile "sample-download/$name"
}
```

`sample-download` のあるディレクトリで、次をPowerShellで実行する。
`evidence-code` が存在しない場所を使う。既存作業のあるディレクトリでcheckoutしない。

```powershell
git clone --filter=blob:none --no-checkout --depth 1 https://github.com/awano27/ai-news-site.git evidence-code
Set-Location evidence-code
git sparse-checkout init --no-cone
git sparse-checkout set /src/__init__.py /src/auto_collect/__init__.py /src/auto_collect/claim_evidence.py /scripts/render_claim_evidence.py
git fetch --depth 1 origin 0b9ad2b115fdcb83291cf7f3f928ff7edba1a708
git checkout --detach 0b9ad2b115fdcb83291cf7f3f928ff7edba1a708
New-Item -ItemType Directory -Path examples -Force | Out-Null
Copy-Item -LiteralPath ../sample-download -Destination examples/claim-evidence -Recurse
```

clone/fetch/checkoutではGitHubから必要なGitデータを取得する。
記事を追加した作業ツリーでは検査対象ページの登録も変わるため、
**説明対象の別チェックアウトで実行する**。ランナーはHEADとコア2ファイルの
LF正規化SHA-256を、対象モジュールのimport前に確認する。
異なる版や変更したコアでは最初のチェックが失敗し、そこで止まる。
import後にも各モジュールの実ファイルがこのチェックアウト内の対象ファイルと一致するか確認する。

## 実行（通信しない）

```powershell
python -B -S examples/claim-evidence/reproduce.py
```

`-B` はPythonキャッシュの作成を抑え、`-S` はsite-packagesを読み込まない。
この条件でも次の12件が通った。Gitの呼出しはローカルHEADの読取りだけで、
実行中にfetchや出典URLの取得は行わない。`example.com` は架空の参照先表記である。

```text
PASS 01 pinned_core
PASS 02 valid_record
PASS 03 statement_change_rejected
PASS 04 conditions_change_rejected
PASS 05 missing_source_rejected
PASS 06 source_record_change_rejected
PASS 07 legacy_without_badge
PASS 08 provenance_not_upgraded
PASS 09 review_metadata_not_authenticated
PASS 10 static_regeneration_identical
PASS 11 implausible_claim_not_truth_checked
PASS 12 subject_and_body_changes_rejected
RESULT 12/12 checks passed; expected rejections were observed.
```

No.03〜06と12は、意図した不整合が拒否されたことの成功である。
予想しない結果の場合だけ、FAILと終了コード1を返す。全件が期待どおりなら終了コード0。

## ケースの読み方

- No.02: 整合した記録が通り、ベンダー公称値・資料との照合済みを表示する。
- No.03〜06: statement、conditions、参照先ID、出典タイトルをそれぞれ独立に変更し、拒否を確認する。保存済みfingerprintは変更しない。
- No.07: `None` / `{}` はエラーにも照合済み表示にもならない。
- No.08: 通常の表示は `vendor_claim` / `ai_document_review` を第三者実測・人による照合へ格上げしない。
- No.09: 架空レコードの確認日・確認方法を別の有効値へ手で変えると、再sealなしでも通り、変更後の人による照合ラベルが表示される。これらはハッシュ対象外で、確認者を認証する機能はない。No.08の「自動変換しない」とは別の限界である。statusも対象外だが、このケースでは変更していない。
- No.10: 静的HTMLを2回レンダリングし、HTML、出典、照合日が不変で、既存チェッカーも通る。
- No.11: 月面での宇宙船組立てという不自然な架空主張でも、構造と保存値が整えば通る。真偽判定をしないことを示す。
- No.12: ニュースのsummary変更はsubject fingerprintで、静的HTMLの本文変更は本文要素との照合で拒否する。

各ケースは初期フィクスチャの深いコピーを使う。初期作成時にだけ記録したsealは
JSON内のリテラルであり、ランナーにsealを更新する処理はない。

## 入出力と後片付け

入力は同梱の `fixtures.json` と固定SHAのコア2ファイル。
標準出力に結果を表示し、静的HTMLの検査に使う一時ディレクトリは終了時に自動削除する。
`-B` によりPythonキャッシュも作らない。本番ページと入力データは書き換えない。

準備で作った `evidence-code` と `sample-download` は残る。
検証を終えて不要になった場合は、親ディレクトリへ戻り、この手順で新規作成した
2フォルダーであることを確認して削除する。既存のリポジトリを削除対象にしない。

## 限界と再利用条件

この検査は真偽判定、出典本文の保存・比較、現在の鮮度確認、電子署名ではない。
権限を持つ編集者による再計算を防がず、対象外の記事の品質も保証しない。
対象SHAでリポジトリ全体のLICENSE/COPYINGは確認できなかったため、
ここで新たな再配布ライセンスを宣言しない。
