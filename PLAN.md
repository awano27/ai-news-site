# 2026-07-25 ヒーロー可読性改善 第2弾 実装計画

## Goal

ルート `index.html` の 768px 以下のヒーローを圧縮し、見出し・本文・本日のトピック・主CTAを 390x844 のファーストビュー内に収める。desktop とフォールバック更新契約は維持する。

## Scope

- Modify: `index.html`
- Modify: `scripts/check_mobile_page_height.py`
- Create: `assets/hero-planck.webp`
- Create: `assets/hero-planck-mobile.webp`
- Create: `outputs/hero_readability_2026-07-25/` の検証ログと3枚のスクリーンショット
- Do not modify: `presentations/index.html`、元画像 `assets/hero-planck.jpg`、DB、remote

## Dependencies and Parallelizable Work

1. 現行の CSS、画像寸法、検証スクリプト、dirty tree、baseline を確認する。
2. Pillow で desktop/mobile WebP を生成する。
3. `index.html` にレスポンシブ CSS、`image-set()`、desktop限定 preload、クレジット可読性を実装する。
4. 既存 Playwright スクリプトを拡張し、mobile/desktop の数値・画像取得・console error・スクリーンショットを保存する。
5. 受け入れ条件、UTF-8 BOM、marker位置、限定diffをレビューする。

画像生成と HTML 実装は独立だが、変更範囲が小さく共有ファイル競合を避けるため直接順次実行する。

## Risks and Mitigations

- desktopデグレ: 画像 preload 以外のモバイル変更を `max-width: 768px` に限定し、1440x900 の baseline と比較する。
- 769〜920pxの急変: 既存の 30vh を 10vh に抑え、769px以上の最低高さは維持する。
- 不要画像取得: desktop preload に `media="(min-width: 769px)"` を付け、mobile用 CSS は mobile WebP と JPEG fallback のみ指定し、PerformanceResourceTiming で確認する。
- marker/JS破損: fallback markerを移動せず、動的書き換え結果と console error をローカルHTTPで確認する。
- dirty tree混入: 指定ファイル以外を編集・stageせず、pushはユーザーの明示指示後に限る。

## Acceptance Criteria and Tests

- 390x844: h1 top 240px以下、hero 680px以下、全高9400px以下、CTA bottom 760px以下。
- 1440x900: hero高さ baseline ±20px、hero-bg幅50%、全高 baseline ±40px、`.res-expand` 非表示。
- mobile WebP 50KB以下、desktop WebP 120KB以下、JPEG保持。
- mobileで取得するhero画像はmobile WebPのみ、desktop preloadはmobileで取得されない。
- console error 0、heroの4項目がfetch成功後に更新、noscriptとfallback marker維持。
- 指定ログと3スクリーンショットを保存し、`git diff --check` と限定diffを確認する。

## Review Checklist

- [x] Functional correctness
- [x] Scope adherence
- [x] Mobile acceptance metrics
- [x] Desktop regression metrics
- [x] Image size and network behavior
- [x] Console and fallback behavior
- [x] UTF-8 BOMなし
- [x] Gitの変更操作/remote操作なし
