#!/usr/bin/env python3
"""Generate day_slide_2026_04_15.html - Chrome Skills story v2 (richer narrative)."""
import base64, os

def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

cover = b64("tmp_0415/cover.jpg")
pages = [b64(f"tmp_0415/page_{i}.jpg") for i in range(15)]

html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Google Chrome Skills：プロンプトを「資産」に変えるAI自動化の新境地 | 2026年4月15日</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #4285F4; --primary-light: #AECBFA; --primary-bright: #669DF6; --primary-deep: #1A73E8;
      --accent: #EA4335; --accent-light: #F6AEA9; --accent-bright: #F28B82;
      --warm: #FBBC04; --warm-light: #FDE293;
      --safe: #34A853; --safe-light: #A8DAB5;
      --danger: #EA4335; --rose: #EC4899;
      --bg-dark: #1A3A7A; --bg-card: #F8FAFC; --border: #E8F0FE;
      --text: #202124; --text-light: #5F6368;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; background: linear-gradient(135deg, #E8F0FE 0%, #F8FAFC 30%, #FEF7E0 70%, #E8F0FE 100%); color: var(--text); line-height: 1.8; padding: 20px; }}
    .container {{ max-width: 1100px; margin: 0 auto; background: white; border-radius: 24px; overflow: hidden; box-shadow: 0 25px 80px rgba(66,133,244,0.12); }}

    header {{ background: linear-gradient(135deg, #1A3A7A 0%, #1A73E8 25%, #EA4335 55%, #FBBC04 80%, #34A853 100%); padding: 56px 48px 48px; position: relative; overflow: hidden; }}
    header::before {{ content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 20% 80%, rgba(102,157,246,0.3) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(251,188,4,0.25) 0%, transparent 50%); }}
    header * {{ position: relative; z-index: 1; }}
    .breaking-badge {{ display: inline-block; background: rgba(102,157,246,0.3); border: 1px solid var(--primary-light); padding: 6px 18px; border-radius: 50px; font-size: 0.85rem; font-weight: 700; color: #E8F0FE; margin-bottom: 20px; }}
    h1 {{ font-size: 2.4rem; font-weight: 900; line-height: 1.4; margin-bottom: 16px; background: linear-gradient(90deg, #ffffff, #AECBFA, #FDE293, #A8DAB5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .subtitle {{ color: #E8F0FE; font-size: 1.1rem; line-height: 1.8; font-weight: 500; }}

    main {{ padding: 48px; }}
    .section {{ margin-bottom: 48px; }}
    .section-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 3px solid var(--border); }}
    .section-icon {{ font-size: 1.8rem; }}
    .section-header h2 {{ font-size: 1.6rem; font-weight: 800; color: var(--primary-deep); }}

    .story-block {{ background: white; border-radius: 16px; padding: 36px; margin-bottom: 32px; border: 2px solid #E8F0FE; box-shadow: 0 4px 16px rgba(66,133,244,0.08); position: relative; }}
    .story-block::before {{ content: attr(data-chapter); position: absolute; top: -14px; left: 32px; background: var(--primary); color: white; padding: 4px 16px; border-radius: 8px; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; }}
    .story-block.ch1 {{ border-left: 5px solid var(--danger); }} .story-block.ch1::before {{ background: var(--danger); }}
    .story-block.ch2 {{ border-left: 5px solid var(--primary); }} .story-block.ch2::before {{ background: var(--primary); }}
    .story-block.ch3 {{ border-left: 5px solid var(--warm); }} .story-block.ch3::before {{ background: var(--warm); }}
    .story-block.ch4 {{ border-left: 5px solid var(--safe); }} .story-block.ch4::before {{ background: var(--safe); }}
    .story-block h3 {{ font-size: 1.4rem; font-weight: 800; margin-bottom: 16px; color: var(--primary-deep); display: flex; align-items: center; gap: 10px; }}
    .story-block p {{ font-size: 1.05rem; line-height: 2; color: #334155; margin-bottom: 12px; }}
    .story-block .scene {{ font-style: italic; color: var(--text-light); background: linear-gradient(135deg, #E8F0FE, #D2E3FC); padding: 16px 20px; border-radius: 10px; margin: 16px 0; border-left: 3px solid var(--primary); }}
    .story-block .metaphor {{ background: linear-gradient(135deg, #FEF7E0, #FEEFC3); padding: 18px 22px; border-radius: 10px; margin: 16px 0; border-left: 4px solid var(--warm); color: #6B4900; font-size: 1rem; line-height: 1.9; }}

    .quote-box.dark {{ background: linear-gradient(135deg, var(--bg-dark), #1A73E8); border: 2px solid var(--warm); color: white; padding: 32px; margin: 32px 0; border-radius: 16px; text-align: center; }}
    .quote-text {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 12px; line-height: 1.9; }}
    .quote-author {{ font-size: 0.95rem; color: var(--warm-light); font-weight: 700; }}

    .highlight-box {{ background: linear-gradient(135deg, rgba(66,133,244,0.06), rgba(251,188,4,0.04)); border-left: 5px solid var(--primary); padding: 24px; margin-bottom: 32px; border-radius: 8px; font-size: 1.05rem; line-height: 1.9; }}
    .highlight-box.accent {{ border-left-color: var(--accent); background: linear-gradient(135deg, rgba(234,67,53,0.06), rgba(234,67,53,0.02)); }}
    .highlight-box.safe {{ border-left-color: var(--safe); background: linear-gradient(135deg, rgba(52,168,83,0.06), rgba(52,168,83,0.02)); }}

    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 32px 0; }}
    .stat-item {{ background: linear-gradient(135deg, var(--bg-dark), #1A73E8); padding: 28px; border-radius: 16px; text-align: center; border: 2px solid rgba(251,188,4,0.5); }}
    .stat-number {{ font-size: 2.2rem; font-weight: 900; color: var(--warm-light); display: block; margin-bottom: 8px; }}
    .stat-label {{ font-size: 0.85rem; color: #AECBFA; font-weight: 600; }}

    .pain-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 32px 0; }}
    .pain-card {{ background: linear-gradient(135deg, #FEF2F2, #FEE2E2); border: 2px solid var(--danger); border-radius: 16px; padding: 24px; }}
    .pain-card .pain-icon {{ font-size: 2rem; margin-bottom: 10px; }}
    .pain-card h3 {{ color: var(--danger); font-size: 1.05rem; margin-bottom: 8px; }}
    .pain-card p {{ color: #7F1D1D; font-size: 0.9rem; line-height: 1.7; }}

    .feature-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 32px 0; }}
    .feature-card {{ background: linear-gradient(135deg, var(--bg-dark), #1A73E8); border-radius: 16px; padding: 28px; text-align: center; color: white; border: 2px solid rgba(102,157,246,0.4); transition: transform 0.3s; }}
    .feature-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(66,133,244,0.25); }}
    .feature-card .f-icon {{ font-size: 2.2rem; margin-bottom: 12px; }}
    .feature-card h3 {{ color: var(--warm-light); font-size: 1.05rem; margin-bottom: 4px; }}
    .feature-card .f-tag {{ display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; background: rgba(234,67,53,0.25); color: var(--accent-light); margin-bottom: 8px; }}
    .feature-card p {{ color: #D2E3FC; font-size: 0.85rem; line-height: 1.6; }}

    .flow-steps {{ display: flex; gap: 12px; align-items: center; justify-content: center; flex-wrap: wrap; margin: 32px 0; }}
    .flow-step {{ background: linear-gradient(135deg, var(--bg-dark), #1A73E8); color: white; padding: 20px 24px; border-radius: 16px; text-align: center; min-width: 150px; border: 2px solid rgba(251,188,4,0.4); }}
    .flow-step .step-num {{ font-size: 0.75rem; color: var(--warm-light); font-weight: 700; margin-bottom: 4px; }}
    .flow-step .step-title {{ font-weight: 800; color: white; font-size: 0.95rem; }}
    .flow-step .step-desc {{ font-size: 0.8rem; color: #AECBFA; margin-top: 4px; }}
    .flow-arrow {{ font-size: 1.5rem; color: var(--primary); font-weight: 900; }}

    .skills-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 32px 0; }}
    .skill-card {{ background: var(--bg-card); border: 2px solid var(--border); border-radius: 12px; padding: 20px; transition: all 0.3s; }}
    .skill-card:hover {{ border-color: var(--primary); transform: translateY(-2px); }}
    .skill-card .s-icon {{ font-size: 1.6rem; margin-bottom: 8px; }}
    .skill-card h4 {{ font-size: 0.92rem; color: var(--primary-deep); margin-bottom: 6px; font-weight: 700; }}
    .skill-card p {{ font-size: 0.78rem; color: var(--text-light); line-height: 1.5; }}

    .evolution-grid {{ display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap: 20px; align-items: center; margin: 32px 0; }}
    .evo-card {{ padding: 24px; border-radius: 16px; text-align: center; }}
    .evo-card.now {{ background: linear-gradient(135deg, #E8F0FE, #D2E3FC); border: 2px solid var(--primary); }}
    .evo-card.next {{ background: linear-gradient(135deg, #FEF7E0, #FDE293); border: 2px solid var(--warm); }}
    .evo-card.future {{ background: linear-gradient(135deg, #E6F4EA, #CEEAD6); border: 2px solid var(--safe); }}
    .evo-card h4 {{ font-size: 0.95rem; font-weight: 800; margin-bottom: 6px; }}
    .evo-card.now h4 {{ color: var(--primary-deep); }}
    .evo-card.next h4 {{ color: #B06000; }}
    .evo-card.future h4 {{ color: #137333; }}
    .evo-card p {{ font-size: 0.82rem; line-height: 1.6; color: #334155; }}
    .evo-arrow {{ font-size: 1.8rem; font-weight: 900; color: var(--primary); }}

    .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 32px 0; }}
    .summary-card {{ background: linear-gradient(135deg, var(--bg-dark), #1A73E8); border-radius: 16px; padding: 28px; text-align: center; color: white; border: 1px solid rgba(251,188,4,0.4); }}
    .summary-card h3 {{ color: var(--warm-light); margin-bottom: 8px; font-size: 1rem; }}
    .summary-card p {{ color: #AECBFA; font-size: 0.85rem; line-height: 1.6; }}
    .summary-icon {{ font-size: 2rem; margin-bottom: 8px; }}

    .slide-img {{ width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.12); border: 1px solid #e0e0e0; display: block; }}
    .inline-slides {{ display: flex; flex-direction: column; gap: 24px; margin: 32px 0; }}

    .links-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 24px 0; }}
    .link-item {{ display: flex; align-items: center; gap: 10px; padding: 14px 18px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; font-size: 0.95rem; }}
    .link-item a {{ color: var(--primary-deep); text-decoration: none; font-weight: 600; }}
    .link-item code {{ background: var(--bg-dark); color: var(--warm-light); padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; }}

    .back-to-top {{ position: fixed; top: 30px; left: 30px; z-index: 1000; background: rgba(26,58,122,0.92); backdrop-filter: blur(12px); padding: 12px 24px; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); border: 1px solid rgba(102,157,246,0.5); display: flex; align-items: center; gap: 10px; color: white; font-weight: 600; font-size: 1rem; text-decoration: none; transition: all 0.3s; }}
    .back-to-top:hover {{ transform: translateY(-3px) scale(1.05); background: rgba(66,133,244,0.92); }}

    footer {{ background: linear-gradient(135deg, #1A3A7A, #1A73E8); padding: 32px 48px; color: #AECBFA; text-align: center; font-size: 0.9rem; }}
    footer a {{ color: var(--warm-light); text-decoration: none; }}

    @media (max-width: 768px) {{
      body {{ padding: 0; }} .container {{ border-radius: 0; }} header {{ padding: 36px 20px; }}
      h1 {{ font-size: 1.8rem; }} main {{ padding: 24px 20px; }}
      .back-to-top {{ top: 15px; left: 15px; padding: 8px 16px; font-size: 0.85rem; }}
      .pain-grid, .feature-grid {{ grid-template-columns: 1fr; }}
      .skills-grid, .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .evolution-grid {{ grid-template-columns: 1fr; }}
      .evo-arrow {{ transform: rotate(90deg); }}
      .story-block {{ padding: 28px 20px; }}
      .flow-steps {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <a href="../../index.html" class="back-to-top">&#x1F3E0; TOPに戻る</a>
  <div class="container">
    <header>
      <div class="breaking-badge">&#x1F3AF; 2026&#x5E74;4&#x6708;15&#x65E5;&#x901F;&#x5831; | Google Chrome Skills &#x2014; &#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x306E;&#x300C;&#x95A2;&#x6570;&#x5316;&#x300D;&#x9769;&#x547D;</div>
      <h1>&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x304C;&#x300C;&#x5C02;&#x5C5E;AI&#x30AA;&#x30DA;&#x30EC;&#x30FC;&#x30BF;&#x30FC;&#x300D;&#x306B; &#x2014; &#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x3092;&#x300C;&#x8CC7;&#x7523;&#x300D;&#x306B;&#x5909;&#x3048;&#x308B;Chrome Skills</h1>
      <p class="subtitle">&#x30DE;&#x30EB;&#x30C1;&#x30BF;&#x30D6;&#x6A2A;&#x65AD;&#x306E;&#x79D2;&#x901F;&#x5316; &#x00D7; &#x601D;&#x8003;&#x30D5;&#x30EC;&#x30FC;&#x30E0;&#x56FA;&#x5B9A; &#x00D7; 50+&#x30D7;&#x30EA;&#x30BB;&#x30C3;&#x30C8; &#x2014; &#x500B;&#x4EBA;&#x306E;&#x30CE;&#x30A6;&#x30CF;&#x30A6;&#x3092;&#x7D44;&#x7E54;&#x306E;&#x300C;&#x8CC7;&#x7523;&#x300D;&#x306B;&#x3057;&#x3001;WebMCP&#x306B;&#x3088;&#x308B;&#x81EA;&#x5F8B;&#x578B;&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;&#x3078;&#x306E;&#x6A4B;&#x6E21;&#x3057;&#x3068;&#x306A;&#x308B;</p>
    </header>

    <main>
      <div class="section">
        <div class="inline-slides">
          <img alt="Chrome Skills&#x30AB;&#x30D0;&#x30FC;" class="slide-img" data-b64-src="data:image/jpeg;base64,{cover}">
        </div>
      </div>

      <!-- CH1: プロンプト入力地獄からのSOS -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F198;</span>
          <h2>&#x7B2C;1&#x7AE0;&#xFF1A;&#x7D42;&#x308F;&#x3089;&#x306A;&#x3044;&#x300C;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x5165;&#x529B;&#x5730;&#x7344;&#x300D;&#x304B;&#x3089;&#x306E;SOS</h2>
        </div>
        <div class="story-block ch1" data-chapter="CHAPTER 1">
          <h3>&#x1F9E0; &#x300C;&#x3082;&#x3046;&#x540C;&#x3058;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x3092;&#x6253;&#x3061;&#x305F;&#x304F;&#x306A;&#x3044;&#x300D;&#x2014;&#x30CA;&#x30EC;&#x30C3;&#x30B8;&#x30EF;&#x30FC;&#x30AB;&#x30FC;&#x306E;&#x60B2;&#x9CF4;</h3>
          <div class="scene">&#x8133;&#x5185;&#x30ED;&#x30B0;&#xFF1A;&#x300C;&#x3053;&#x306E;&#x8A18;&#x4E8B;&#x30923;&#x884C;&#x3067;&#x8981;&#x7D04;&#x3057;&#x3066;&#x300D;&#x300C;&#x3053;&#x306E;&#x30BF;&#x30D6;&#x3068;&#x3042;&#x306E;&#x30BF;&#x30D6;&#x306E;&#x30B9;&#x30DA;&#x30C3;&#x30AF;&#x3092;&#x8868;&#x3067;&#x6BD4;&#x8F03;&#x3057;&#x3066;&#x300D;&#x2014;&#x2014; &#x5358;&#x8ABF;&#x306A;&#x30EB;&#x30FC;&#x30D7;&#x306B;&#x9676;&#x9154;&#x3057;&#x3001;&#x6B21;&#x306E;&#x601D;&#x8003;&#x306B;&#x9032;&#x3081;&#x306A;&#x3044;&#x2026;&#x2026;</div>
          <p>&#x73FE;&#x4EE3;&#x306E;IT&#x30A8;&#x30F3;&#x30B8;&#x30CB;&#x30A2;&#x3001;PM&#x3001;&#x30EA;&#x30B5;&#x30FC;&#x30C1;&#x30E3;&#x30FC;&#x306E;&#x65E5;&#x5E38;&#x306F;&#x3001;&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x306E;&#x7121;&#x6570;&#x306E;&#x30BF;&#x30D6;&#x3068;&#x683C;&#x95D8;&#x3059;&#x308B;&#x65E5;&#x3005;&#x3067;&#x3059;&#x3002;&#x6280;&#x8853;&#x8A18;&#x4E8B;&#x306E;&#x7406;&#x89E3;&#x3001;SaaS&#x306E;&#x6A5F;&#x80FD;&#x6BD4;&#x8F03;&#x3001;&#x6C42;&#x4EBA;&#x7968;&#x306E;&#x8A55;&#x4FA1;&#x3001;&#x7AF6;&#x5408;&#x30B5;&#x30A4;&#x30C8;&#x306E;&#x5206;&#x6790;&#x2026;&#x2026;&#x3042;&#x3089;&#x3086;&#x308B;&#x30BF;&#x30B9;&#x30AF;&#x3067;<strong>&#x300C;&#x6BCE;&#x56DE;&#x30BC;&#x30ED;&#x304B;&#x3089;&#x540C;&#x3058;&#x3088;&#x3046;&#x306A;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x3092;&#x6253;&#x3061;&#x8FBC;&#x3080;&#x300D;</strong>&#x3053;&#x3068;&#x304C;&#x5F53;&#x305F;&#x308A;&#x524D;&#x306B;&#x306A;&#x3063;&#x3066;&#x3044;&#x307E;&#x3057;&#x305F;&#x3002;</p>
          <p>&#x3057;&#x304B;&#x3082;&#x5C11;&#x3057;&#x6307;&#x793A;&#x304C;&#x5909;&#x308F;&#x308B;&#x3060;&#x3051;&#x3067;&#x51FA;&#x529B;&#x30D5;&#x30A9;&#x30FC;&#x30DE;&#x30C3;&#x30C8;&#x304C;&#x30D6;&#x30EC;&#x3066;&#x3057;&#x307E;&#x3044;&#x3001;&#x6BD4;&#x8F03;&#x3084;&#x84C4;&#x7A4D;&#x304C;&#x3057;&#x306B;&#x304F;&#x304F;&#x306A;&#x308B;&#x3002;&#x62E1;&#x5F35;&#x6A5F;&#x80FD;&#x3084;RPA&#x3092;&#x99C6;&#x4F7F;&#x3057;&#x3066;&#x3082;<strong>WebUI&#x306E;&#x5909;&#x66F4;&#x306B;&#x5F31;&#x304F;&#x3001;&#x4FDD;&#x5B88;&#x306B;&#x30B3;&#x30B9;&#x30C8;&#x304C;&#x304B;&#x304B;&#x308B;</strong>&#x3002;&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x4E0A;&#x306E;&#x53CD;&#x5FA9;&#x4F5C;&#x696D;&#x3092;&#x30B7;&#x30FC;&#x30E0;&#x30EC;&#x30B9;&#x306B;&#x81EA;&#x52D5;&#x5316;&#x3059;&#x308B;&#x306E;&#x306F;&#x3001;&#x3053;&#x308C;&#x307E;&#x3067;&#x3069;&#x3046;&#x3057;&#x3066;&#x3082;&#x56F0;&#x96E3;&#x3060;&#x3063;&#x305F;&#x306E;&#x3067;&#x3059;&#x3002;</p>
        </div>

        <div class="pain-grid">
          <div class="pain-card">
            <div class="pain-icon">&#x1F501;</div>
            <h3>&#x540C;&#x3058;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x306E;&#x518D;&#x5165;&#x529B;</h3>
            <p>&#x6BCE;&#x56DE;&#x30BC;&#x30ED;&#x304B;&#x3089;&#x300C;3&#x884C;&#x8981;&#x7D04;&#x300D;&#x300C;&#x6BD4;&#x8F03;&#x8868;&#x300D;&#x3092;&#x6253;&#x3061;&#x8FBC;&#x3080;&#x7121;&#x99C4;&#x3001;&#x601D;&#x8003;&#x306E;&#x5206;&#x65AD;</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon">&#x1F4DD;</div>
            <h3>&#x51FA;&#x529B;&#x30D5;&#x30A9;&#x30FC;&#x30DE;&#x30C3;&#x30C8;&#x306E;&#x30D6;&#x30EC;</h3>
            <p>&#x6307;&#x793A;&#x304C;&#x5FAE;&#x5999;&#x306B;&#x7570;&#x306A;&#x308B;&#x3068;&#x51FA;&#x529B;&#x5F62;&#x5F0F;&#x304C;&#x5909;&#x5316;&#x3057;&#x3001;&#x6BD4;&#x8F03;&#x3082;&#x84C4;&#x7A4D;&#x3082;&#x56F0;&#x96E3;</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon">&#x1F9E9;</div>
            <h3>RPA/&#x62E1;&#x5F35;&#x6A5F;&#x80FD;&#x306E;&#x8106;&#x5F31;&#x3055;</h3>
            <p>WebUI&#x5909;&#x66F4;&#x306B;&#x5F31;&#x304F;&#x3001;&#x4FDD;&#x5B88;&#x30B3;&#x30B9;&#x30C8;&#x304C;&#x591A;&#x304F;&#x3001;&#x30B7;&#x30FC;&#x30E0;&#x30EC;&#x30B9;&#x306A;&#x81EA;&#x52D5;&#x5316;&#x306F;&#x4E0D;&#x53EF;&#x80FD;</p>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="&#x8AB2;&#x984C;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[1]}">
          <img alt="&#x554F;&#x984C;&#x8A73;&#x7D30;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[2]}">
        </div>
      </div>

      <!-- CH2: 魔法の杖（関数） -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1FA84;</span>
          <h2>&#x7B2C;2&#x7AE0;&#xFF1A;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x304C;&#x300C;&#x9B54;&#x6CD5;&#x306E;&#x6756;&#xFF08;&#x95A2;&#x6570;&#xFF09;&#x300D;&#x306B;&#x5909;&#x308F;&#x308B;&#x65E5;</h2>
        </div>
        <div class="story-block ch2" data-chapter="CHAPTER 2">
          <h3>&#x1F3AF; 2026&#x5E74;4&#x6708;14&#x65E5;&#x3001;Google Chrome Skills &#x6B63;&#x5F0F;&#x767B;&#x5834;</h3>
          <p>&#x3053;&#x306E;&#x975E;&#x52B9;&#x7387;&#x306A;&#x65E5;&#x5E38;&#x3092;&#x6253;&#x7834;&#x3059;&#x308B;&#x89E3;&#x6C7A;&#x7B56;&#x3068;&#x3057;&#x3066;&#x3001;Google&#x306F;<strong>&#x300C;Google Chrome Skills&#x300D;</strong>&#x3092;&#x6B63;&#x5F0F;&#x306B;&#x5C0E;&#x5165;&#x3057;&#x307E;&#x3057;&#x305F;&#x3002;&#x3088;&#x304F;&#x4F7F;&#x3046;Gemini&#x3078;&#x306E;&#x6307;&#x793A;&#xFF08;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#xFF09;&#x3092;<strong>&#x300CSkill&#x300D;</strong>&#x3068;&#x3057;&#x3066;&#x4FDD;&#x5B58;&#x3057;&#x3001;&#x30EF;&#x30F3;&#x30AF;&#x30EA;&#x30C3;&#x30AF;&#x3084;<code>/</code>&#x30B3;&#x30DE;&#x30F3;&#x30C9;&#x3067;&#x5373;&#x5EA7;&#x306B;&#x518D;&#x5229;&#x7528;&#x3067;&#x304D;&#x308B;&#x6A5F;&#x80FD;&#x3067;&#x3059;&#x3002;</p>
          <div class="metaphor">
            &#x1F4D6; &#x4F8B;&#x3048;&#x308B;&#x306A;&#x3089;&#x3001;<strong>&#x6BCE;&#x56DE;&#x30EC;&#x30B7;&#x30D4;&#x3092;&#x691C;&#x7D22;&#x3057;&#x76F4;&#x3059;&#x624B;&#x9593;&#x3092;&#x7701;&#x304D;&#x3001;&#x304A;&#x6C17;&#x306B;&#x5165;&#x308A;&#x306E;&#x6599;&#x7406;&#x672C;&#x306E;&#x91CD;&#x8981;&#x306A;&#x30DA;&#x30FC;&#x30B8;&#x306B;&#x4ED8;&#x7B8B;&#x3092;&#x8CBC;&#x3063;&#x3066;&#x3044;&#x3064;&#x3067;&#x3082;&#x4E00;&#x77AC;&#x3067;&#x958B;&#x3051;&#x308B;&#x3088;&#x3046;&#x306B;&#x3059;&#x308B;&#x611F;&#x899A;</strong>&#x3067;&#x3059;&#x3002;&#x305D;&#x306E;&#x5834;&#x9650;&#x308A;&#x306E;&#x300C;&#x4F1A;&#x8A71;&#x300D;&#x3060;&#x3063;&#x305F;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x304C;&#x3001;&#x3044;&#x3064;&#x3067;&#x3082;&#x547C;&#x3073;&#x51FA;&#x305B;&#x308B;&#x300C;&#x518D;&#x5229;&#x7528;&#x53EF;&#x80FD;&#x306A;&#x64CD;&#x4F5C;&#xFF08;&#x95A2;&#x6570;&#xFF09;&#x300D;&#x3078;&#x3068;&#x6607;&#x683C;&#x3057;&#x307E;&#x3057;&#x305F;&#x3002;
          </div>
        </div>

        <div class="flow-steps">
          <div class="flow-step">
            <div class="step-num">STEP 1</div>
            <div class="step-title">AI&#x3068;&#x5BFE;&#x8A71;</div>
            <div class="step-desc">&#x30B5;&#x30A4;&#x30C9;&#x30D1;&#x30CD;&#x30EB;&#x3067;Gemini&#x306B;&#x6307;&#x793A;</div>
          </div>
          <div class="flow-arrow">&#x27A1;&#xFE0F;</div>
          <div class="flow-step">
            <div class="step-num">STEP 2</div>
            <div class="step-title">Save as Skill</div>
            <div class="step-desc">&#x6C17;&#x306B;&#x5165;&#x3063;&#x305F;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x3092;&#x4FDD;&#x5B58;</div>
          </div>
          <div class="flow-arrow">&#x27A1;&#xFE0F;</div>
          <div class="flow-step">
            <div class="step-num">STEP 3</div>
            <div class="step-title">/&#x30B3;&#x30DE;&#x30F3;&#x30C9;</div>
            <div class="step-desc">&#x30B9;&#x30E9;&#x30C3;&#x30B7;&#x30E5;&#x3067;&#x5373;&#x547C;&#x3073;&#x51FA;&#x3057;</div>
          </div>
          <div class="flow-arrow">&#x27A1;&#xFE0F;</div>
          <div class="flow-step">
            <div class="step-num">STEP 4</div>
            <div class="step-title">&#x8CC7;&#x7523;&#x5316;</div>
            <div class="step-desc">&#x4F7F;&#x3044;&#x6368;&#x3066;&#x2192;&#x518D;&#x5229;&#x7528;&#x95A2;&#x6570;</div>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="Chrome Skills&#x6982;&#x8981;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[3]}">
          <img alt="&#x4FDD;&#x5B58;&#x65B9;&#x6CD5;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[4]}">
        </div>
      </div>

      <!-- CH3: 専属AIオペレーター -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F9D1;&#x200D;&#x1F4BB;</span>
          <h2>&#x7B2C;3&#x7AE0;&#xFF1A;&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x304C;&#x300C;&#x5C02;&#x5C5E;AI&#x30AA;&#x30DA;&#x30EC;&#x30FC;&#x30BF;&#x30FC;&#x300D;&#x3068;&#x3057;&#x3066;&#x6A5F;&#x80FD;&#x3059;&#x308B;&#x65E5;&#x5E38;</h2>
        </div>
        <div class="story-block ch3" data-chapter="CHAPTER 3">
          <h3>&#x26A1; 3&#x3064;&#x306E;&#x9769;&#x547D;&#x7684;&#x306A;&#x5909;&#x5316;</h3>
          <p>Skills&#x3092;&#x624B;&#x306B;&#x5165;&#x308C;&#x305F;&#x30E6;&#x30FC;&#x30B6;&#x30FC;&#x306E;&#x30EF;&#x30FC;&#x30AF;&#x30D5;&#x30ED;&#x30FC;&#x306F;&#x3001;&#x5287;&#x7684;&#x306B;&#x9032;&#x5316;&#x3057;&#x307E;&#x3059;&#x3002;&#x30BF;&#x30D6;&#x306E;&#x307E;&#x307E;&#x3001;&#x30EF;&#x30F3;&#x30AF;&#x30EA;&#x30C3;&#x30AF;&#x3067;&#x300C;&#x5C02;&#x5C5E;&#x306E;&#x30AA;&#x30DA;&#x30EC;&#x30FC;&#x30BF;&#x30FC;&#x300D;&#x304C;&#x4F55;&#x3067;&#x3082;&#x3084;&#x3063;&#x3066;&#x304F;&#x308C;&#x308B;&#x611F;&#x899A;&#x3067;&#x3059;&#x3002;</p>
        </div>

        <div class="feature-grid">
          <div class="feature-card">
            <div class="f-icon">&#x1F4CA;</div>
            <h3>&#x30DE;&#x30EB;&#x30C1;&#x30BF;&#x30D6;&#x6A2A;&#x65AD;&#x306E;&#x79D2;&#x901F;&#x5316;</h3>
            <div class="f-tag">&#x6700;&#x5927;10&#x30BF;&#x30D6;</div>
            <p>&#x8907;&#x6570;&#x30BF;&#x30D6;&#x3092;&#x958B;&#x3044;&#x305F;&#x307E;&#x307E;&#x300C;&#x30B9;&#x30DA;&#x30C3;&#x30AF;&#x6BD4;&#x8F03;&#x8868;&#x300D;&#x3092;&#x5B9F;&#x884C;&#x3002;&#x30EA;&#x30B5;&#x30FC;&#x30C1;&#x6642;&#x9593;&#x304C;<strong>&#x534A;&#x5206;&#x4EE5;&#x4E0B;</strong>&#x306B;&#x5727;&#x7E2E;</p>
          </div>
          <div class="feature-card">
            <div class="f-icon">&#x1F9E0;</div>
            <h3>&#x300C;&#x7B2C;&#x4E8C;&#x306E;&#x8133;&#x300D;&#x3078;&#x76F4;&#x7D50;</h3>
            <div class="f-tag">Markdown&#x51FA;&#x529B;</div>
            <p>&#x51FA;&#x529B;&#x30D5;&#x30A9;&#x30FC;&#x30DE;&#x30C3;&#x30C8;&#x3092;&#x56FA;&#x5B9A;&#x3057;&#x3001;Obsidian&#x30FBNotion&#x3078;&#x69CB;&#x9020;&#x5316;&#x30C7;&#x30FC;&#x30BF;&#x3068;&#x3057;&#x3066;&#x76F4;&#x63A5;&#x84C4;&#x7A4D;</p>
          </div>
          <div class="feature-card">
            <div class="f-icon">&#x1F4DA;</div>
            <h3>50+&#x30D7;&#x30EA;&#x30BB;&#x30C3;&#x30C8;&#x30EA;&#x30DF;&#x30C3;&#x30AF;&#x30B9;</h3>
            <div class="f-tag">&#x30CE;&#x30FC;&#x30B3;&#x30FC;&#x30C9;</div>
            <p>Protein Maximizer / YouTube Summarizer / &#x6C42;&#x4EBA;&#x8A55;&#x4FA1;&#x3092;&#x81EA;&#x5206;&#x7528;&#x306B;&#x300C;&#x30EA;&#x30DF;&#x30C3;&#x30AF;&#x30B9;&#x300D;</p>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item"><span class="stat-number">10&#x30BF;&#x30D6;</span><span class="stat-label">&#x540C;&#x6642;&#x6A2A;&#x65AD;&#x53EF;&#x80FD;</span></div>
          <div class="stat-item"><span class="stat-number">50+</span><span class="stat-label">&#x30D7;&#x30EA;&#x30BB;&#x30C3;&#x30C8;Skill</span></div>
          <div class="stat-item"><span class="stat-number">1/2</span><span class="stat-label">&#x30EA;&#x30B5;&#x30FC;&#x30C1;&#x6642;&#x9593;&#x5727;&#x7E2E;</span></div>
          <div class="stat-item"><span class="stat-number">0&#x884C;</span><span class="stat-label">&#x30CE;&#x30FC;&#x30B3;&#x30FC;&#x30C9;&#x3067;&#x81EA;&#x52D5;&#x5316;</span></div>
        </div>

        <h3 style="font-size:1.15rem; color:var(--primary-deep); margin:32px 0 16px; font-weight:800;">&#x1F4BC; &#x30A8;&#x30F3;&#x30B8;&#x30CB;&#x30A2;&#x30FBPM&#x5411;&#x3051;&#x5B9F;&#x7528;&#x30E6;&#x30FC;&#x30B9;&#x30B1;&#x30FC;&#x30B9;</h3>
        <div class="skills-grid">
          <div class="skill-card">
            <div class="s-icon">&#x1F4C4;</div>
            <h4>&#x6280;&#x8853;&#x8A18;&#x4E8B;&#x307E;&#x3068;&#x3081;</h4>
            <p>3&#x884C;&#x8981;&#x7D04;+&#x5B9F;&#x88C5;&#x30DD;&#x30A4;&#x30F3;&#x30C8;&#x62BD;&#x51FA;&#x2192;Obsidian</p>
          </div>
          <div class="skill-card">
            <div class="s-icon">&#x1F4CA;</div>
            <h4>&#x7AF6;&#x5408;&#x6BD4;&#x8F03;&#x5206;&#x6790;</h4>
            <p>&#x30BF;&#x30D6;&#x3092;&#x6A2A;&#x65AD;&#x3057;&#x3066;Markdown&#x8868;&#x3067;&#x51FA;&#x529B;</p>
          </div>
          <div class="skill-card">
            <div class="s-icon">&#x1F4BB;</div>
            <h4>&#x30B3;&#x30FC;&#x30C9;&#x30EC;&#x30D3;&#x30E5;&#x30FC;</h4>
            <p>GitHub&#x304B;&#x3089;&#x554F;&#x984C;&#x70B9;&#x30FB;&#x6539;&#x5584;&#x6848;&#x62BD;&#x51FA;</p>
          </div>
          <div class="skill-card">
            <div class="s-icon">&#x1F4DD;</div>
            <h4>&#x8A2D;&#x8A08;&#x30EC;&#x30D3;&#x30E5;&#x30FC;</h4>
            <p>&#x30C9;&#x30AD;&#x30E5;&#x30E1;&#x30F3;&#x30C8;&#x3092;WBS&#x5316;&#x2192;Notion</p>
          </div>
        </div>

        <div class="inline-slides">
          <img alt="3&#x3064;&#x306E;&#x6A5F;&#x80FD;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[5]}">
          <img alt="&#x30DE;&#x30EB;&#x30C1;&#x30BF;&#x30D6;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[6]}">
          <img alt="&#x30D7;&#x30EA;&#x30BB;&#x30C3;&#x30C8;&#x6D3B;&#x7528;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[8]}">
          <img alt="&#x30E6;&#x30FC;&#x30B9;&#x30B1;&#x30FC;&#x30B9;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[10]}">
        </div>
      </div>

      <!-- CH4: 資産化と自律型エージェント -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F3DB;&#xFE0F;</span>
          <h2>&#x7B2C;4&#x7AE0;&#xFF1A;&#x5C5E;&#x4EBA;&#x7684;&#x306A;&#x30CE;&#x30A6;&#x30CF;&#x30A6;&#x304B;&#x3089;&#x3001;&#x7D44;&#x7E54;&#x306E;&#x300C;&#x8CC7;&#x7523;&#x300D;&#x3068;&#x300C;&#x81EA;&#x5F8B;&#x578B;&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;&#x300D;&#x3078;</h2>
        </div>
        <div class="story-block ch4" data-chapter="EPILOGUE">
          <h3>&#x1F310; Skill&#x30AB;&#x30BF;&#x30ED;&#x30B0;&#x3092;&#x7D44;&#x7E54;&#x3067;&#x5171;&#x6709;&#x3057;&#x3001;WebMCP&#x3067;&#x81EA;&#x5F8B;&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;&#x3078;</h3>
          <p>Chrome Skills&#x304C;&#x3082;&#x305F;&#x3089;&#x3059;&#x7A76;&#x6975;&#x306E;&#x4FA1;&#x5024;&#x306F;&#x3001;&#x500B;&#x4EBA;&#x306E;&#x982D;&#x306E;&#x4E2D;&#x306B;&#x3042;&#x3063;&#x305F;&#x30CE;&#x30A6;&#x30CF;&#x30A6;&#x3084;&#x512A;&#x308C;&#x305F;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x304C;<strong>&#x300C;&#x518D;&#x5229;&#x7528;&#x53EF;&#x80FD;&#x306A;&#x8CC7;&#x7523;&#x300D;</strong>&#x306B;&#x5909;&#x308F;&#x308B;&#x3053;&#x3068;&#x3067;&#x3059;&#x3002;&#x4F5C;&#x6210;&#x3057;&#x305F;Skill&#x3092;&#x30C1;&#x30FC;&#x30E0;&#x3067;&#x5171;&#x6709;&#xFF08;<strong>Skill&#x30AB;&#x30BF;&#x30ED;&#x30B0;&#x5316;</strong>&#xFF09;&#x3059;&#x308C;&#x3070;&#x3001;&#x8AB0;&#x3067;&#x3082;&#x6700;&#x9AD8;&#x54C1;&#x8CEA;&#x306E;&#x30EA;&#x30B5;&#x30FC;&#x30C1;&#x3084;&#x30B3;&#x30FC;&#x30C9;&#x30EC;&#x30D3;&#x30E5;&#x30FC;&#x3092;&#x518D;&#x73FE;&#x3067;&#x304D;&#x308B;&#x3088;&#x3046;&#x306B;&#x306A;&#x308A;&#x307E;&#x3059;&#x3002;</p>
          <p>&#x66F4;&#x306B;&#x91CD;&#x8981;&#x306A;&#x306E;&#x304C;<strong>&#x300CWebMCP&#xFF08;Web Model Context Protocol&#xFF09;&#x300D;</strong>&#x3067;&#x3059;&#x3002;AI&#x304C;&#x753B;&#x9762;&#x3092;&#x63A8;&#x6E2C;&#x3059;&#x308B;&#x306E;&#x3067;&#x306F;&#x306A;&#x304F;&#x3001;Web&#x30B5;&#x30A4;&#x30C8;&#x5074;&#x306E;&#x6A5F;&#x80FD;&#x3092;<em>API&#x30EC;&#x30D9;&#x30EB;&#x3067;&#x76F4;&#x63A5;&#x5B89;&#x5168;&#x306B;&#x547C;&#x3073;&#x51FA;&#x3059;</em>&#x4ED5;&#x7D44;&#x307F;&#x304C;&#x88CF;&#x5074;&#x3067;&#x52D5;&#x3044;&#x3066;&#x3044;&#x307E;&#x3059;&#x3002;&#x3053;&#x308C;&#x306F;&#x5C06;&#x6765;&#x7684;&#x306B;AI&#x304C;&#x81EA;&#x5F8B;&#x7684;&#x306B;&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x3092;&#x64CD;&#x4F5C;&#x3057;&#x3066;&#x30BF;&#x30B9;&#x30AF;&#x3092;&#x5B8C;&#x9042;&#x3059;&#x308B;<strong>&#x300CAuto Browse&#x300D;</strong>&#x306A;&#x3069;&#x306E;&#x5B8C;&#x5168;&#x81EA;&#x5F8B;&#x578B;&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;&#x3078;&#x306E;&#x6975;&#x3081;&#x3066;&#x91CD;&#x8981;&#x306A;&#x6A4B;&#x6E21;&#x3057;&#x3068;&#x306A;&#x308A;&#x307E;&#x3059;&#x3002;</p>
        </div>

        <div class="evolution-grid">
          <div class="evo-card now">
            <h4>&#x1F4CD; &#x4ECA;</h4>
            <p>&#x500B;&#x4EBA;&#x30EC;&#x30D9;&#x30EB;&#x306E;Skill&#x4FDD;&#x5B58;&#x30FB;&#x547C;&#x3073;&#x51FA;&#x3057;</p>
          </div>
          <div class="evo-arrow">&#x27A1;&#xFE0F;</div>
          <div class="evo-card next">
            <h4>&#x1F4BC; &#x6B21;</h4>
            <p>Skill&#x30AB;&#x30BF;&#x30ED;&#x30B0;&#x3067;&#x30C1;&#x30FC;&#x30E0;&#x696D;&#x52D9;&#x3092;&#x6A19;&#x6E96;&#x5316;</p>
          </div>
          <div class="evo-arrow">&#x27A1;&#xFE0F;</div>
          <div class="evo-card future">
            <h4>&#x1F680; &#x5C06;&#x6765;</h4>
            <p>WebMCP&#x00D7;Auto Browse&#x3067;&#x81EA;&#x5F8B;&#x578B;&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;</p>
          </div>
        </div>

        <div class="quote-box dark">
          <div class="quote-text">&#x300C;&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x306F;&#x4F7F;&#x3044;&#x6368;&#x3066;&#x306E;&#x547E;&#x6587;&#x3067;&#x306F;&#x306A;&#x304F;&#x3001;&#x30C1;&#x30FC;&#x30E0;&#x3067;&#x5171;&#x6709;&#x3067;&#x304D;&#x308B;&#x300E;&#x547D;&#x4EE4;&#x30BB;&#x30C3;&#x30C8;&#x300F;&#x3068;&#x3044;&#x3046;&#x8CC7;&#x7523;&#x306B;&#x306A;&#x308B;&#x300D;</div>
          <div class="quote-author">&#x2014; Chrome Skills&#x304C;&#x6697;&#x306B;&#x793A;&#x3059;&#x672A;&#x6765;</div>
        </div>

        <div class="highlight-box safe">
          <strong>&#x1F4A1; &#x65E9;&#x671F;&#x4F53;&#x9A13;&#x306E;&#x30D2;&#x30F3;&#x30C8;&#xFF08;2026&#x5E74;4&#x6708;&#x73FE;&#x5728;&#xFF09;&#xFF1A;</strong><br>
          &#x30C7;&#x30B9;&#x30AF;&#x30C8;&#x30C3;&#x30D7;&#x7248;Chrome&#x306E;&#x8A00;&#x8A9E;&#x8A2D;&#x5B9A;&#x3092;<strong>&#x300CEnglish (US)&#x300D;</strong>&#x306B;&#x5207;&#x308A;&#x66FF;&#x3048;&#x308B;&#x3053;&#x3068;&#x3067;&#x3001;&#x3053;&#x306E;&#x9769;&#x65B0;&#x7684;&#x306A;&#x6A5F;&#x80FD;&#x3092;&#x3044;&#x3061;&#x65E9;&#x304F;&#x4F53;&#x9A13;&#x3067;&#x304D;&#x307E;&#x3059;&#x3002;&#x30D6;&#x30E9;&#x30A6;&#x30B6;&#x306F;&#x3082;&#x306F;&#x3084;&#x5358;&#x306A;&#x308B;&#x95B2;&#x89A7;&#x30BD;&#x30D5;&#x30C8;&#x3067;&#x306F;&#x306A;&#x304F;&#x3001;&#x3042;&#x306A;&#x305F;&#x306E;&#x601D;&#x8003;&#x3092;&#x62E1;&#x5F35;&#x3059;&#x308B;<em>&#x300CAI&#x30EF;&#x30FC;&#x30AF;&#x30B9;&#x30C6;&#x30FC;&#x30B7;&#x30E7;&#x30F3;&#x300D;</em>&#x3078;&#x9032;&#x5316;&#x3057;&#x307E;&#x3057;&#x305F;&#x3002;
        </div>

        <div class="inline-slides">
          <img alt="&#x8CC7;&#x7523;&#x5316;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[11]}">
          <img alt="&#x30C1;&#x30FC;&#x30E0;&#x5171;&#x6709;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[12]}">
          <img alt="&#x672A;&#x6765;&#x5C55;&#x671B;" class="slide-img" data-b64-src="data:image/jpeg;base64,{pages[14]}">
        </div>

        <div class="links-grid">
          <div class="link-item">&#x1F517; <a href="https://gemini.google/overview/gemini-in-chrome/" target="_blank">Gemini in Chrome &#x516C;&#x5F0F;</a></div>
          <div class="link-item">&#x1F4DA; <code>chrome://skills/browse</code>&#xFF08;&#x516C;&#x5F0F;&#x30E9;&#x30A4;&#x30D6;&#x30E9;&#x30EA;&#xFF09;</div>
          <div class="link-item">&#x2699;&#xFE0F; <code>chrome://skills</code>&#xFF08;&#x81EA;&#x5206;&#x306E;Skill&#x7BA1;&#x7406;&#xFF09;</div>
          <div class="link-item">&#x1F4F0; <a href="https://9to5google.com" target="_blank">9to5Google / Digital Trends &#x7D39;&#x4ECB;</a></div>
        </div>
      </div>

      <!-- まとめ -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">&#x1F3AF;</span>
          <h2>&#x672C;&#x65E5;&#x306E;&#x307E;&#x3068;&#x3081;</h2>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-icon">&#x1FA84;</div>
            <h3>&#x95A2;&#x6570;&#x5316;</h3>
            <p>&#x30D7;&#x30ED;&#x30F3;&#x30D7;&#x30C8;&#x3092;&#x547C;&#x3073;&#x51FA;&#x3057;&#x53EF;&#x80FD;&#x306A;Skill&#x306B;&#x5909;&#x63DB;</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x1F4CA;</div>
            <h3>10&#x30BF;&#x30D6;&#x6A2A;&#x65AD;</h3>
            <p>&#x30DE;&#x30EB;&#x30C1;&#x30BF;&#x30D6;&#x6BD4;&#x8F03;&#x3092;1&#x30AF;&#x30EA;&#x30C3;&#x30AF;&#x3067;&#x81EA;&#x52D5;&#x751F;&#x6210;</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x1F9E0;</div>
            <h3>&#x7B2C;&#x4E8C;&#x306E;&#x8133;&#x9023;&#x643A;</h3>
            <p>Markdown&#x51FA;&#x529B;&#x3067;Obsidian&#x30FBNotion&#x3078;&#x76F4;&#x84C4;&#x7A4D;</p>
          </div>
          <div class="summary-card">
            <div class="summary-icon">&#x1F680;</div>
            <h3>WebMCP&#x3078;</h3>
            <p>&#x81EA;&#x5F8B;&#x578B;AI&#x30A8;&#x30FC;&#x30B8;&#x30A7;&#x30F3;&#x30C8;&#x3078;&#x306E;&#x6A4B;&#x6E21;&#x3057;</p>
          </div>
        </div>
      </div>
    </main>
    <footer>
      <p>&#x1F4C5; 2026&#x5E74;4&#x6708;15&#x65E5; AI&#x30CB;&#x30E5;&#x30FC;&#x30B9;&#x901F;&#x5831; | <a href="../day_slides_index.html">&#x30B9;&#x30E9;&#x30A4;&#x30C9;&#x4E00;&#x89A7;</a> | <a href="../../index.html">TOP</a></p>
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

path = "presentations/day_slides/day_slide_2026_04_15.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Generated: {path} ({os.path.getsize(path)/1024/1024:.1f}MB)")
