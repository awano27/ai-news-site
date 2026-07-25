# 2026-07-25 トップページ モバイル高さ短縮 実装計画

## Goal

ルート `index.html` のモバイル表示だけを圧縮し、リソースを3枚から展開可能にする。desktop表示、11本のリンク、JavaScript無効時の表示を維持する。

## Scope

- Modify: `index.html`
- Create: `scripts/check_mobile_page_height.py`
- Create: `outputs/mobile_height_2026-07-25/` の検証ログと3枚のスクリーンショット
- Do not modify: `presentations/index.html`、リソースカードの順序・内容、remote、DB

## Dependencies and Sequence

1. 現在のCSS、HTML、IIFE、dirty treeを確認する。
2. 768px以下限定のpadding、折りたたみ、展開ボタンを実装する。
3. Python検証スクリプトを作成し、ローカルHTTPサーバーとPlaywright Chromiumで測定する。
4. mobile/desktopの数値、カード枚数、button、console、DOMリンク数を受け入れ条件と照合する。
5. `git diff --check` と限定diffレビューを行う。

## Risks and Mitigations

- desktopデグレ: すべての新規レイアウト規則を `max-width: 768px` 内に限定し、1440pxで実測する。
- JavaScript無効時の欠落: `is-collapsed` はHTMLに書かず、IIFEでのみ付与する。
- dirty tree混入: `index.html`、`PLAN.md`、指定の新規script/output以外を編集・stageしない。
- file URLのfetch制約: localhostの一時HTTPサーバーをスクリプト内で起動する。

## Acceptance Criteria

- 390x844: 全高9700px以下、初期3枚、展開後11枚、button 44px以上。
- 1440x900: 全高7400〜7650px、11枚3カラム、button非表示。
- console error 0、リソースリンク11本、静的HTMLに `is-collapsed` なし。
- desktop各対象sectionの高さが既知のbaselineから±20px以内。
- UTF-8 BOMなし、カードの削除・並べ替えなし、Git/remote操作なし。

## Review Checklist

- [x] Functional correctness
- [x] Scope adherence
- [x] Accessibility and no-JS fallback
- [x] Mobile and desktop measurements
- [x] Console/link regressions
- [x] Maintainable inline CSS/var-based IIFE
