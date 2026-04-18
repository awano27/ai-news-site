#!/usr/bin/env python3
"""Generate day_slide_2026_04_17.html - Claude Opus 4.7 v2 (richer content incl. Claude Design)."""
import base64, os

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

cover = b64("tmp_0417/cover.jpg")
pages = [b64(f"tmp_0417/page_{i}.jpg") for i in range(19)]

html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Opus 4.7：次世代自律型知能の実装・移行完全ガイド | 2026年4月17日</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #6D28D9; --primary-light: #C4B5FD; --primary-bright: #A78BFA; --primary-deep: #4C1D95;
      --accent: #0EA5E9; --accent-light: #BAE6FD; --accent-bright: #38BDF8;
      --warm: #F59E0B; --warm-light: #FDE293;
      --danger: #DC2626; --safe: #059669; --safe-light: #6EE7B7;
      --cyan: #06B6D4; --rose: #DB2777;
      --bg-dark: #1E1B4B; --bg-card: #F5F3FF; --border: #DDD6FE;
      --text: #1C1917; --text-light: #57534E;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 30%, #E0F2FE 70%, #F5F3FF 100%); color: var(--text); line-height: 1.8; padding: 20px; }}
    .container {{ max-width: 1100px; margin: 0 auto; background: white; border-radius: 24px; overflow: hidden; box-shadow: 0 25px 80px rgba(109,40,217,0.12); }}

    header {{ background: linear-gradient(135deg, #1E1B4B 0%, #4C1D95 30%, #6D28D9 60%, #0EA5E9 100%); padding: 56px 48px 48px; position: relative; overflow: hidden; }}
    header::before {{ content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 25% 80%, rgba(167,139,250,0.3) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(14,165,233,0.25) 0%, transparent 50%); }}
    header * {{ position: relative; z-index: 1; }}
    .breaking-badge {{ display: inline-block; background: rgba(167,139,250,0.3); border: 1px solid var(--primary-light); padding: 6px 18px; border-radius: 50px; font-size: 0.85rem; font-weight: 700; color: #EDE9FE; margin-bottom: 20px; }}
    .version-tag {{ display: inline-block; background: rgba(14,165,233,0.3); border: 1px solid var(--accent-light); padding: 4px 14px; border-radius: 6px; font-size: 0.8rem; font-weight: 800; color: var(--accent-bright); margin-left: 10px; letter-spacing: 1px; }}
    h1 {{ font-size: 2.4rem; font-weight: 900; line-height: 1.4; margin-bottom: 16px; background: linear-gradient(90deg, #fff, #C4B5FD, #BAE6FD); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .subtitle {{ color: #DDD6FE; font-size: 1.1rem; line-height: 1.8; font-weight: 500; }}

    main {{ padding: 48px; }}
    .section {{ margin-bottom: 48px; }}
    .section-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 3px solid var(--border); }}
    .section-icon {{ font-size: 1.8rem; }}
    .section-header h2 {{ font-size: 1.6rem; font-weight: 800; color: var(--primary-deep); }}

    .upgrade-banner {{ background: linear-gradient(135deg, var(--bg-dark), #4C1D95); border: 2px solid var(--primary-bright); border-radius: 16px; padding: 32px; margin-bottom: 32px; display: flex; align-items: center; gap: 24px; }}
    .upgrade-banner .ub-ver {{ font-size: 3rem; font-weight: 900; color: var(--primary-bright); white-space: nowrap; }}
    .upgrade-banner .ub-desc {{ color: #DDD6FE; font-size: 1rem; line-height: 1.7; }}
    .upgrade-banner .ub-desc strong {{ color: white; }}

    .hero-feature {{ background: linear-gradient(135deg, #F5F3FF, #EDE9FE); border: 3px solid var(--primary); border-radius: 20px; padding: 36px; margin: 32px 0; position: relative; overflow: hidden; }}
    .hero-feature::before {{ content: 'FLAGSHIP NEW'; position: absolute; top: -12px; right: 32px; background: linear-gradient(135deg, var(--danger), var(--rose)); color: white; padding: 6px 16px; border-radius: 8px; font-size: 0.75rem; font-weight: 900; letter-spacing: 2px; }}
    .hero-feature h3 {{ color: var(--primary-deep); font-size: 1.6rem; margin-bottom: 12px; font-weight: 900; display: flex; align-items: center; gap: 12px; }}
    .hero-feature p {{ color: #334155; font-size: 1.02rem; line-height: 1.9; margin-bottom: 16px; }}
    .hero-feature .hf-flow {{ display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin-top: 20px; }}
    .hf-step {{ background: white; border: 2px solid var(--primary-light); border-radius: 12px; padding: 16px 20px; flex: 1; min-width: 180px; text-align: center; }}
    .hf-step .hf-n {{ font-size: 0.7rem; color: var(--primary); font-weight: 800; margin-bottom: 4px; }}
    .hf-step .hf-t {{ font-weight: 800; color: var(--primary-deep); font-size: 0.95rem; margin-bottom: 4px; }}
    .hf-step .hf-d {{ font-size: 0.78rem; color: var(--text-light); line-height: 1.5; }}
    .hf-arrow {{ font-size: 1.4rem; color: var(--primary); align-self: center; }}

    .new-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 32px 0; }}
    .new-card {{ background: var(--bg-card); border: 2px solid var(--border); border-radius: 16px; padding: 28px; position: relative; }}
    .new-card .new-badge {{ position: absolute; top: -10px; right: 20px; background: var(--danger); color: white; padding: 3px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; letter-spacing: 1px; }}
    .new-card .n-icon {{ font-size: 1.8rem; margin-bottom: 10px; }}
    .new-card h3 {{ color: var(--primary-deep); font-size: 1.1rem; margin-bottom: 8px; font-weight: 800; }}
    .new-card p {{ color: var(--text-light); font-size: 0.92rem; line-height: 1.7; }}
    .new-card code {{ background: var(--bg-dark); color: var(--accent-bright); padding: 2px 8px; border-radius: 4px; font-size: 0.82rem; }}

    .improve-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 32px 0; }}
    .improve-card {{ background: linear-gradient(135deg, var(--bg-dark), #4C1D95); border-radius: 16px; padding: 28px; text-align: center; color: white; border: 2px solid rgba(167,139,250,0.35); transition: transform 0.3s; }}
    .improve-card:hover {{ transform: translateY(-4px); }}
    .improve-card .i-icon {{ font-size: 2.2rem; margin-bottom: 12px; }}
    .improve-card h3 {{ color: var(--primary-bright); font-size: 1.05rem; margin-bottom: 4px; }}
    .improve-card .i-metric {{ display: inline-block; padding: 4px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 800; background: rgba(14,165,233,0.25); color: var(--accent-bright); margin: 6px 0 10px; }}
    .improve-card p {{ color: #DDD6FE; font-size: 0.85rem; line-height: 1.6; }}

    .bench-table {{ width: 100%; border-collapse: collapse; margin: 24px 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }}
    .bench-table th {{ background: linear-gradient(135deg, var(--primary-deep), var(--primary)); color: white; padding: 14px 18px; text-align: left; font-weight: 700; font-size: 0.9rem; }}
    .bench-table td {{ padding: 14px 18px; border-top: 1px solid var(--border); font-size: 0.92rem; }}
    .bench-table tr:hover {{ background: #FAF5FF; }}
    .bench-table .bench-up {{ color: var(--safe); font-weight: 800; }}
    .bench-table .bench-down {{ color: var(--danger); font-weight: 800; }}
    .bench-table .bench-same {{ color: var(--warm); font-weight: 700; }}

    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 32px 0; }}
    .stat-item {{ background: linear-gradient(135deg, var(--bg-dark), #4C1D95); padding: 28px; border-radius: 16px; text-align: center; border: 2px solid rgba(167,139,250,0.5); }}
    .stat-number {{ font-size: 2.2rem; font-weight: 900; color: var(--accent-bright); display: block; margin-bottom: 8px; }}
    .stat-label {{ font-size: 0.85rem; color: #DDD6FE; font-weight: 600; }}

    .usecase-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 32px 0; }}
    .usecase-card {{ background: var(--bg-card); border: 2px solid var(--border); border-radius: 16px; padding: 28px; border-left: 5px solid var(--primary); }}
    .usecase-card .u-icon {{ font-size: 2rem; margin-bottom: 10px; }}
    .usecase-card h3 {{ color: var(--primary-deep); font-size: 1.1rem; margin-bottom: 8px; font-weight: 800; }}
    .usecase-card p {{ color: var(--text-light); font-size: 0.9rem; line-height: 1.8; }}
    .usecase-card .u-tag {{ display: inline-block; background: var(--primary-light); color: var(--primary-deep); padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; margin-right: 4px; margin-top: 6px; }}

    .warning-box {{ background: linear-gradient(135deg, #FEF2F2, #FEE2E2); border: 2px solid var(--danger); border-left: 6px solid var(--danger); padding: 24px; margin: 24px 0; border-radius: 12px; }}
    .warning-box h3 {{ color: var(--danger); font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
    .warning-box p {{ color: #7F1D1D; font-size: 0.95rem; line-height: 1.8; }}
    .warning-box ul {{ color: #7F1D1D; padding-left: 20px; line-height: 1.9; font-size: 0.95rem; }}
    .warning-box code {{ background: #451A03; color: #FDE68A; padding: 2px 8px; border-radius: 4px; font-size: 0.82rem; }}
    .warning-box.caution {{ background: linear-gradient(135deg, #FFFBEB, #FEF3C7); border-color: var(--warm); border-left-color: var(--warm); }}
    .warning-box.caution h3 {{ color: #92400E; }}
    .warning-box.caution p, .warning-box.caution ul {{ color: #78350F; }}

    .highlight-box {{ background: linear-gradient(135deg, rgba(109,40,217,0.06), rgba(14,165,233,0.04)); border-left: 5px solid var(--primary); padding: 24px; margin-bottom: 32px; border-radius: 8px; font-size: 1.05rem; line-height: 1.9; }}
    .highlight-box.accent {{ border-left-color: var(--accent); background: linear-gradient(135deg, rgba(14,165,233,0.06), rgba(14,165,233,0.02)); }}

    .quote-box.dark {{ background: linear-gradient(135deg, var(--bg-dark), #0C4A6E); border: 2px solid var(--primary-bright); color: white; padding: 32px; margin: 32px 0; border-radius: 16px; text-align: center; }}
    .quote-text {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 12px; line-height: 1.9; }}
    .quote-author {{ font-size: 0.95rem; color: var(--accent-bright); font-weight: 700; }}

    .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 32px 0; }}
    .summary-card {{ background: linear-gradient(135deg, var(--bg-dark), #4C1D95); border-radius: 16px; padding: 28px; text-align: center; color: white; border: 1px solid rgba(167,139,250,0.4); }}
    .summary-card h3 {{ color: var(--accent-bright); margin-bottom: 8px; font-size: 1rem; }}
    .summary-card p {{ color: #DDD6FE; font-size: 0.85rem; line-height: 1.6; }}
    .summary-icon {{ font-size: 2rem; margin-bottom: 8px; }}

    .slide-img {{ width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.12); border: 1px solid #e0e0e0; display: block; }}
    .inline-slides {{ display: flex; flex-direction: column; gap: 24px; margin: 32px 0; }}
    .back-to-top {{ position: fixed; top: 30px; left: 30px; z-index: 1000; background: rgba(30,27,75,0.92); backdrop-filter: blur(12px); padding: 12px 24px; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); border: 1px solid rgba(167,139,250,0.5); color: white; font-weight: 600; font-size: 1rem; text-decoration: none; transition: all 0.3s; display: flex; align-items: center; gap: 10px; }}
    .back-to-top:hover {{ transform: translateY(-3px) scale(1.05); background: rgba(109,40,217,0.92); }}
    footer {{ background: linear-gradient(135deg, #1E1B4B, #0C4A6E); padding: 32px 48px; color: #DDD6FE; text-align: center; font-size: 0.9rem; }}
    footer a {{ color: var(--accent-bright); text-decoration: none; }}

    @media (max-width: 768px) {{
      body {{ padding: 0; }} .container {{ border-radius: 0; }} header {{ padding: 36px 20px; }}
      h1 {{ font-size: 1.8rem; }} main {{ padding: 24px 20px; }}
      .back-to-top {{ top: 15px; left: 15px; padding: 8px 16px; font-size: 0.85rem; }}
      .new-grid, .improve-grid, .usecase-grid {{ grid-template-columns: 1fr; }}
      .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .upgrade-banner {{ flex-direction: column; text-align: center; }}
      .bench-table {{ font-size: 0.8rem; }} .bench-table th, .bench-table td {{ padding: 10px 12px; }}
    }}
  </style>
</head>
<body>
  <a href="../../index.html" class="back-to-top">&#x1F3E0; TOPに戻る</a>
  <div class="container">
    <header>
      <div class="breaking-badge">&#x1F680; 2026年4月17日速報 | Claude Opus 4.7 リリース<span class="version-tag">v4.7 GA</span></div>
      <h1>次世代自律型知能 Claude Opus 4.7 — 実装・移行完全ガイド</h1>
      <p class="subtitle">コーディング能力13%向上 × 視覚精度98.5% × 新ツール「Claude Design」登場 — 自己検証で人間の監視不要、Mythos Preview商用版として登場した最強フラッグシップ</p>
    </header>

    <main>
      <div class="section">
        <div class="inline-slides">
          <img alt="Opus 4.7 カバー" class="slide-img" data-b64-src="data:image/jpeg;base64,{cover}">
        </div>
      </div>

      <!-- バージョンアップ概要 -->
      <div class="section">
        <div class="upgrade-banner">
          <div class="ub-ver">4.6 &#x27A1;&#xFE0F; 4.7</div>
          <div class="ub-desc">
            <strong>SWE-bench Pro 53.4% → 64.3%</strong>（企業コードベース相当の難度）、<strong>XBOW視覚ベンチ 54.5% → 98.5%</strong>、<strong>解像度3倍（最大2,576px）</strong>。自己検証能力と「Claude Design」の登場で、AIは「テキスト生成」から「自律型知能エンジン」へと変貌。Mythos Previewの商用版として、サイバー能力にセーフガードを施した最強モデル。
          </div>
        </div>
      </div>

      <!-- Claude Design（目玉機能） -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F3A8;</span>
          <h2>&#x1F195; 目玉の新プロダクト「Claude Design」（研究プレビュー）</h2>
        </div>

        <div class="hero-feature">
          <h3>&#x2728; テキストからUIを生成・微調整 &#x2192; Claude Codeへ即実装</h3>
          <p>Opus 4.7の強力なビジョン能力を駆動エンジンとし、自然言語の指示だけで<strong>Webプロトタイプ、プレゼンスライド、1ページャー</strong>などを即座に生成できる新ツール。非デザイナーのPMでもアイデアを数分で動くプロトタイプへ。</p>
          <div class="hf-flow">
            <div class="hf-step"><div class="hf-n">STEP 1</div><div class="hf-t">自然言語で生成</div><div class="hf-d">「ダークテーマのSaaSランディング」等</div></div>
            <div class="hf-arrow">&#x27A1;&#xFE0F;</div>
            <div class="hf-step"><div class="hf-n">STEP 2</div><div class="hf-t">Tweaks（微調整）</div><div class="hf-d">余白・色・Glowをスライダーで直感操作</div></div>
            <div class="hf-arrow">&#x27A1;&#xFE0F;</div>
            <div class="hf-step"><div class="hf-n">STEP 3</div><div class="hf-t">Claude Codeへ</div><div class="hf-d">1クリックでTailwind/Reactへ実装</div></div>
            <div class="hf-arrow">&#x27A1;&#xFE0F;</div>
            <div class="hf-step"><div class="hf-n">STEP 4</div><div class="hf-t">エクスポート</div><div class="hf-d">Canva連携 / PDF / PPTX</div></div>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="Claude Design" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[10]}">
          <img alt="Tweaks機能" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[11]}">
        </div>
      </div>

      <!-- その他の新機能 -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F195;</span>
          <h2>&#x2728; その他の新機能・新要素</h2>
        </div>

        <div class="new-grid">
          <div class="new-card">
            <div class="new-badge">NEW</div>
            <div class="n-icon">&#x1F50D;</div>
            <h3>Claude Code <code>/ultrareview</code></h3>
            <p>ブランチ全体や変更差分を読み込み、<strong>並列マルチエージェントでクラウド上で包括的レビュー</strong>。バグ・設計問題をプロのレビュアーレベルで指摘。</p>
          </div>
          <div class="new-card">
            <div class="new-badge">NEW</div>
            <div class="n-icon">&#x1F916;</div>
            <h3>Autoモード（Max限定）</h3>
            <p>途中の承認プロンプトをスキップして<strong>長時間自律実行</strong>。Maxプランユーザー向けに正式解放。リポジトリ横断の大規模作業に最適。</p>
          </div>
          <div class="new-card">
            <div class="new-badge">NEW</div>
            <div class="n-icon">&#x1F9EA;</div>
            <h3>推論レベル <code>xhigh</code></h3>
            <p><code>high</code>と<code>max</code>の中間に新設。<strong>コーディングやエージェント用途</strong>での利用が推奨。深さとレイテンシのバランスを細かく制御。</p>
          </div>
          <div class="new-card">
            <div class="new-badge">BETA</div>
            <div class="n-icon">&#x1F4B5;</div>
            <h3>Task budgets</h3>
            <p>全体のトークン消費「目安（予算）」をモデル自身に意識させ、<strong>自律的にペース配分</strong>。エージェントループの暴走とコスト爆発を予防。</p>
          </div>
          <div class="new-card">
            <div class="new-badge">NEW</div>
            <div class="n-icon">&#x1F6E1;&#xFE0F;</div>
            <h3>Cyber Verification Program</h3>
            <p>Mythos Preview由来の強力なサイバー能力にセーフガード。<strong>正当な脆弱性調査・ペネトレーションテスト専門家</strong>向けに機能をアンロックする認証プログラム。</p>
          </div>
          <div class="new-card">
            <div class="new-badge">NEW</div>
            <div class="n-icon">&#x1F30D;</div>
            <h3>データレジデンシー（inference_geo）</h3>
            <p>推論地域を指定可能に。US/EU等のコンプライアンス要件に対応し、<strong>エンタープライズ/公共機関での導入障壁</strong>を大幅に低減。</p>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="新機能概要" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[1]}">
          <img alt="xhigh / Task budgets" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[4]}">
          <img alt="ultrareview" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[13]}">
        </div>
      </div>

      <!-- 性能改善 -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F4C8;</span>
          <h2>&#x2B06;&#xFE0F; 性能改善 — 自己検証と高解像度ビジョン</h2>
        </div>

        <div class="improve-grid">
          <div class="improve-card">
            <div class="i-icon">&#x1F9E0;</div>
            <h3>自己検証能力</h3>
            <div class="i-metric">Self-verification</div>
            <p>出力を報告する前に自ら検証方法を考案し、論理的欠陥を検知・修正。就寝中に任せきれる粘り強さ</p>
          </div>
          <div class="improve-card">
            <div class="i-icon">&#x1F441;&#xFE0F;</div>
            <h3>高解像度ビジョン</h3>
            <div class="i-metric">1,568 &#x2192; 2,576px</div>
            <p>3倍以上に拡張。金融ダッシュボード、化学構造式、システム図をピクセル単位で正確に読み取り</p>
          </div>
          <div class="improve-card">
            <div class="i-icon">&#x1F4CB;</div>
            <h3>指示追従の厳密化</h3>
            <div class="i-metric">Literal interpretation</div>
            <p>「よしなに」推測を排除。指示にないことは勝手に実行しない規律。プロンプト再調整を推奨</p>
          </div>
        </div>

        <h3 style="font-size:1.15rem; color:var(--primary-deep); margin:32px 0 12px; font-weight:800;">&#x1F4CA; 主要ベンチマーク比較（Opus 4.7 vs 4.6 vs GPT-5.4）</h3>
        <table class="bench-table">
          <thead>
            <tr>
              <th>カテゴリ</th>
              <th>Opus 4.7</th>
              <th>Opus 4.6</th>
              <th>GPT-5.4</th>
              <th>変化</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Agentic coding</strong>（SWE-bench Pro）</td>
              <td>64.3%</td>
              <td>53.4%</td>
              <td>57.7%</td>
              <td class="bench-up">&#x2B06;&#xFE0F; +10.9pt</td>
            </tr>
            <tr>
              <td><strong>Visual reasoning</strong>（XBOW）</td>
              <td>98.5%</td>
              <td>54.5%</td>
              <td>—</td>
              <td class="bench-up">&#x2B06;&#xFE0F; +44.0pt</td>
            </tr>
            <tr>
              <td><strong>Visual acuity</strong>（XBOW）</td>
              <td>82.1%</td>
              <td>75.1%</td>
              <td>—</td>
              <td class="bench-up">&#x2B06;&#xFE0F; +7.0pt</td>
            </tr>
            <tr>
              <td><strong>Multidisciplinary reasoning</strong></td>
              <td>46.9%</td>
              <td>40.0%</td>
              <td>43.9%</td>
              <td class="bench-up">&#x2B06;&#xFE0F; +6.9pt</td>
            </tr>
            <tr>
              <td><strong>BigLaw Bench</strong>（法務）</td>
              <td>90.9%</td>
              <td>—</td>
              <td>—</td>
              <td class="bench-same">&#x1F3C6; 新記録</td>
            </tr>
          </tbody>
        </table>

        <div class="inline-slides">
          <img alt="ベンチマーク" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[2]}">
          <img alt="ビジョン強化" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[5]}">
          <img alt="自己検証" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[6]}">
        </div>
      </div>

      <!-- ユースケース -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F4BC;</span>
          <h2>&#x1F3AF; ユースケース — 実用レベルに到達した4つの領域</h2>
        </div>

        <div class="usecase-grid">
          <div class="usecase-card">
            <div class="u-icon">&#x1F4BB;</div>
            <h3>長手数の自律型コーディング</h3>
            <p>リポジトリ横断のリファクタリング、複雑なバグ調査、CI/CD自律構築。自己検証でAIに任せきり、<strong>人間の監視不要</strong>。</p>
            <span class="u-tag">Agentic coding</span>
            <span class="u-tag">CI/CD</span>
          </div>
          <div class="usecase-card">
            <div class="u-icon">&#x1F3A8;</div>
            <h3>Design to Code完全自動化</h3>
            <p>Claude DesignでUI生成 &#x2192; TweaksでGlow・余白調整 &#x2192; Claude CodeでTailwind/Reactとして実装。<strong>PMでも数分でプロトタイプ</strong>。</p>
            <span class="u-tag">Claude Design</span>
            <span class="u-tag">Tailwind</span>
          </div>
          <div class="usecase-card">
            <div class="u-icon">&#x1F5BC;&#xFE0F;</div>
            <h3>高精細画像・図面解析</h3>
            <p>解像度3倍で化学構造式・システム図・金融ダッシュボードをピクセル単位読み取り。<strong>Computer Use（PC自動操作）の精度</strong>も向上。</p>
            <span class="u-tag">Vision</span>
            <span class="u-tag">Computer Use</span>
          </div>
          <div class="usecase-card">
            <div class="u-icon">&#x1F3E5;</div>
            <h3>医療・金融・法務（エンタープライズ）</h3>
            <p>HIPAA/ICD-10対応、MS Office/S&amp;P Global/FactSet MCPコネクタ。<strong>BigLaw Bench 90.9%</strong>で契約条項の厳密な読み分け。</p>
            <span class="u-tag">HIPAA</span>
            <span class="u-tag">MCP</span>
            <span class="u-tag">BigLaw 90.9%</span>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="ユースケース" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[14]}">
          <img alt="エンタープライズ" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[16]}">
        </div>
      </div>

      <!-- 移行時の注意 -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x26A0;&#xFE0F;</span>
          <h2>&#x1F6A8; 移行に関する重要事項（Migration Check）</h2>
        </div>

        <div class="warning-box">
          <h3>&#x26D4; API破壊的変更 — 移行前に必ず対応</h3>
          <ul>
            <li><strong>サンプリングパラメータ廃止</strong>：<code>temperature</code>/<code>top_p</code>/<code>top_k</code>をデフォルト以外に指定すると<strong>400エラー</strong>。挙動はプロンプトで制御</li>
            <li><strong>思考モード変更</strong>：<code>budget_tokens</code>廃止 &#x2192; <code>adaptive thinking</code>に一本化（モデル自動調整）</li>
            <li><strong>プレフィル廃止</strong>：アシスタントメッセージ書き出し指定が400エラー &#x2192; <strong>Structured Outputs</strong>へ移行</li>
            <li><strong>トークン消費増加</strong>：新トークナイザーで同入力でも<strong>1.0〜1.35倍に増加</strong>（価格は$5/$25据え置きだが実質コスト増）</li>
          </ul>
        </div>

        <div class="warning-box caution">
          <h3>&#x26A0;&#xFE0F; 注意：MRCR v2スコア低下 — 用途によってはOpus 4.6を継続検討</h3>
          <p>超長文脈の単純検索ベンチマーク「MRCR v2」でOpus 4.6からスコア低下。Anthropicは「意図的なノイズで騙す実務と乖離した指標」とし<strong>「Graphwalks」</strong>（コードベース探索のような実務的推論）への移行を推進。ただし、<strong>大量の雑多な文書からの単純検索用途</strong>ではOpus 4.6の方が適している場合あり。</p>
        </div>

        <div class="highlight-box accent">
          <strong>&#x1F4DD; 移行チェックリスト：</strong><br>
          1. <code>temperature</code>/<code>top_p</code>/<code>top_k</code>パラメータを削除<br>
          2. <code>budget_tokens</code> &#x2192; <code>adaptive thinking</code>へ書き換え<br>
          3. プレフィル利用箇所を<strong>Structured Outputs</strong>へ移行<br>
          4. トークン消費量を<strong>1.35倍</strong>で再見積もり、レート制限バッファ確認<br>
          5. プロンプトを「曖昧→明示的」に書き換え（literal解釈対応）<br>
          6. MRCR型の単純検索用途は<strong>Opus 4.6継続を検討</strong>
        </div>

        <div class="inline-slides">
          <img alt="破壊的変更" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[8]}">
          <img alt="トークン増" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[9]}">
          <img alt="MRCR注意" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[17]}">
        </div>
      </div>

      <!-- エピローグ -->
      <div class="section">
        <div class="quote-box dark">
          <div class="quote-text">「AIは"質問に答える"段階を超え、"自ら設計し、自ら検証し、自ら実装する"自律型知能エンジンになった」</div>
          <div class="quote-author">— Claude Opus 4.7 Autonomous Engine</div>
        </div>

        <div class="inline-slides">
          <img alt="まとめ" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[18]}">
        </div>
      </div>

      <!-- まとめ -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F3AF;</span>
          <h2>本日のまとめ</h2>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-icon">&#x1F3A8;</div>
            <h3>Claude Design</h3>
            <p>テキスト→UI→Tailwind/ReactをAIで完全自動化</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x1F9E0;</div>
            <h3>自己検証 +10.9pt</h3>
            <p>SWE-bench Pro 53.4%→64.3%、就寝中AIに任せきり</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x1F441;&#xFE0F;</div>
            <h3>3倍ビジョン</h3>
            <p>2,576px、XBOW視覚98.5%でCompute Useも進化</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x26A0;&#xFE0F;</div>
            <h3>API破壊的変更</h3>
            <p>temperature/prefill廃止、トークン1.35倍、MRCR低下</p>
          </div>
        </div>
      </div>
    </main>
    <footer>
      <p>&#x1F4C5; 2026年4月17日 AIニュース速報 | <a href="../day_slides_index.html">スライド一覧</a> | <a href="../../index.html">TOP</a></p>
    </footer>
  </div>
  <script>
    document.querySelectorAll('img[data-b64-src]').forEach(img => {{
      const b64 = img.getAttribute('data-b64-src');
      if (b64) {{ img.src = b64; img.removeAttribute('data-b64-src'); }}
    }});
  </script>
</body>
</html>'''

path = "presentations/day_slides/day_slide_2026_04_17.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Generated: {path} ({os.path.getsize(path)/1024/1024:.1f}MB)")
