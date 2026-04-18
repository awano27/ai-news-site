/*
 * news.js — AI Intelligence Hub
 * ------------------------------------------------------------
 * Purpose:
 *   Progressively enhances existing news / archive pages by
 *   injecting a "Claude Code 活用ポイント" (Claude Code takeaway)
 *   callout under each news card. This adds editorial depth
 *   and strengthens E-E-A-T (Experience) signals for AdSense.
 *
 * Usage:
 *   <script src="/ai-news-site/assets/js/news.js" defer></script>
 *
 * Targets (auto-detected, first match wins):
 *   [data-news-item]               ← preferred
 *   article.news-card, .news-item  ← legacy fallbacks
 *
 * Safety:
 *   - Idempotent (data-cc-injected flag)
 *   - Works on static HTML (no framework required)
 *   - Compatible with GitHub Pages + .nojekyll
 * ------------------------------------------------------------
 */
(function () {
  'use strict';

  var CALLOUT_CLASS = 'cc-callout';
  var FLAG_ATTR = 'data-cc-injected';

  // Topic -> Claude Code takeaway mapping. Keyword matching is
  // case-insensitive and checks title + summary text.
  var RULES = [
    { kw: /claude\s*code/i,           msg: 'Claude Code なら /plan でこの発表内容を自分のリポジトリへ適用する手順をそのまま生成できます。' },
    { kw: /anthropic|claude/i,         msg: 'Claude Code から Anthropic API を呼び出すサンプルは <code>anthropic</code> SDK で数行。プロンプトキャッシュで料金も圧縮できます。' },
    { kw: /openai|gpt/i,               msg: 'Claude Code で OpenAI 互換 SDK のラッパーを書けば、同じワークフローでモデル比較が可能です。' },
    { kw: /gemini|google\s*ai/i,       msg: 'Claude Code の MCP 経由で Google AI Studio の生成結果を Claude にパイプできます。' },
    { kw: /agent|エージェント/i,        msg: 'Claude Code の Subagent 機能を使うと、このタイプのエージェントを数分で試作できます。' },
    { kw: /rag|検索拡張|ベクトル/i,     msg: 'Claude Code + context-mode MCP でローカル RAG を即席構築できます。' },
    { kw: /コード生成|copilot|ide/i,   msg: 'Claude Code は IDE 拡張(VS Code / JetBrains)でも動作。ターミナル派はそのまま CLI で使えます。' },
    { kw: /mcp|model\s*context/i,      msg: 'Claude Code は MCP サーバ接続が標準装備。このツールも MCP 経由で連携すれば1コマンドで呼べます。' },
    { kw: /benchmark|ベンチマーク/i,   msg: 'Claude Code に自分のタスクを渡して同じベンチを回せば、記事の数字が自分のケースに当てはまるかすぐ検証できます。' },
    { kw: /資金調達|投資|ipo|買収/i,  msg: 'ニュースの一次ソース（S-1 / 決算資料）を Claude Code に読ませ、要点抽出を自動化すると調査時間を1/10に短縮できます。' }
  ];

  var DEFAULT_MSG = '運営者は Claude Code でこのニュースの一次ソースを要約し、自分の業務に当てはまるポイントだけを抜き出して利用しています。';

  function pickMessage(text) {
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i].kw.test(text)) return RULES[i].msg;
    }
    return DEFAULT_MSG;
  }

  function extractText(node) {
    // Prefer title + summary if structured, else entire innerText
    var parts = [];
    var title = node.querySelector('[data-news-title], .news-title, h2, h3');
    var summary = node.querySelector('[data-news-summary], .news-summary, .summary, p');
    if (title)   parts.push(title.textContent || '');
    if (summary) parts.push(summary.textContent || '');
    if (!parts.length) parts.push(node.textContent || '');
    return parts.join(' ').slice(0, 800);
  }

  function buildCallout(msg) {
    var box = document.createElement('div');
    box.className = CALLOUT_CLASS;
    box.setAttribute('role', 'note');
    box.innerHTML =
      '<strong class="cc-badge">Claude Code 活用ポイント</strong>' +
      '<span class="cc-msg">' + msg + '</span>';
    return box;
  }

  function injectStyle() {
    if (document.getElementById('cc-callout-style')) return;
    var s = document.createElement('style');
    s.id = 'cc-callout-style';
    s.textContent =
      '.cc-callout{display:block;margin:14px 0 4px;padding:12px 14px;' +
      'background:rgba(94,231,223,.08);border-left:3px solid #5EE7DF;' +
      'border-radius:8px;font-size:14px;line-height:1.7;color:inherit}' +
      '.cc-callout .cc-badge{display:inline-block;margin-right:8px;padding:2px 8px;' +
      'background:#FFCC00;color:#111;border-radius:999px;font-size:12px;font-weight:800;' +
      'letter-spacing:.02em}' +
      '.cc-callout .cc-msg{color:inherit}' +
      '.cc-callout code{background:rgba(255,255,255,.08);padding:1px 6px;border-radius:4px;' +
      'font-size:.92em}';
    document.head.appendChild(s);
  }

  function enhance(root) {
    root = root || document;
    var selectors = [
      '[data-news-item]',
      'article.news-card',
      '.news-item',
      '.archive-item',
      'article[data-date]'
    ];
    var nodes = root.querySelectorAll(selectors.join(','));
    if (!nodes.length) return 0;

    injectStyle();

    var count = 0;
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.getAttribute(FLAG_ATTR) === '1') continue;
      var text = extractText(n);
      if (!text) continue;
      n.appendChild(buildCallout(pickMessage(text)));
      n.setAttribute(FLAG_ATTR, '1');
      count++;
    }
    return count;
  }

  // Public API so other scripts can re-run after dynamic loads
  window.AIHubNews = window.AIHubNews || {};
  window.AIHubNews.enhanceClaudeCallouts = enhance;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { enhance(); });
  } else {
    enhance();
  }

  // Re-run after late JSON renders (news_archive.html fetches data async)
  document.addEventListener('aihub:news-rendered', function (e) {
    enhance(e && e.target ? e.target : document);
  });
})();
