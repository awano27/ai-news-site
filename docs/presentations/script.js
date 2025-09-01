(() => {
  const state = { persona: 'engineer', activeLabel: 'all', tier: 'all', minScore: 0, search: '' };
  const labelPriority = ['x','must_read','recommended','consider','skip'];
  const labelText = { x:'X最新', must_read:'必読', recommended:'注目', consider:'参考', skip:'見送り' };
  let allArticles = [];
  let filtered = [];

  const $ = (s, r=document)=>r.querySelector(s); const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));

  function extractDomain(u){try{const host=new URL(u).hostname.toLowerCase();const multi=['co.jp','ne.jp','or.jp','ac.jp','go.jp','co.uk','org.uk','gov.uk'];if(multi.some(s=>host.endsWith(s))){const ps=host.split('.');return ps.slice(-3).join('.')}const ps=host.split('.');return ps.slice(-2).join('.')}catch(e){return ''}}
  function faviconUrl(d){return d?`https://www.google.com/s2/favicons?domain=${encodeURIComponent(d)}&sz=32`:''}
  function isXLike(a){return (typeof a.source==='string' && a.source.startsWith('X(')) || (Array.isArray(a.tags)&&a.tags.includes('x_post'))}
  function getLabel(a, persona){ if(isXLike(a)) return 'x'; if(a.label) return a.label; const ev=a.evaluation&&a.evaluation[persona]; return (ev&&ev.recommendation)||'consider'; }
  function getScore(a, persona){ const ev=a.evaluation&&a.evaluation[persona]; if(ev&&typeof ev.total_score==='number') return Math.round(ev.total_score*100); if(typeof a.score==='number'){const s=Math.max(0,Math.min(100,a.score)); return Math.round(s);} return 0; }
  function formatRelative(iso){ if(!iso) return ''; const d=new Date(iso); if(isNaN(d)) return ''; const diff=(Date.now()-d.getTime())/1000; if(diff<60)return'たった今'; if(diff<3600)return`${Math.floor(diff/60)}分前`; if(diff<86400)return`${Math.floor(diff/3600)}時間前`; if(diff<604800)return`${Math.floor(diff/86400)}日前`; const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,'0'),day=String(d.getDate()).padStart(2,'0'); return `${y}/${m}/${day}`; }
  function escapeHtml(t){const d=document.createElement('div'); d.textContent=t??''; return d.innerHTML;}

  function normalizeItem(raw){
    const domain = extractDomain(raw.url||'') || raw.sourceDomain || '';
    const published = raw.publishedAt || raw.published_date || '';
    // Build evaluation object compatible with our UI
    let evaluation = raw.evaluation || {};
    if (evaluation && (evaluation.engineer_score || evaluation.business_score || evaluation.score_breakdown)) {
      evaluation = {
        engineer: {
          total_score: typeof evaluation.engineer_score==='number' ? evaluation.engineer_score : 0,
          breakdown: evaluation.score_breakdown || {}
        },
        business: {
          total_score: typeof evaluation.business_score==='number' ? evaluation.business_score : 0,
          breakdown: evaluation.score_breakdown || {}
        }
      };
    }
    return {
      id: raw.id || `${domain}-${(raw.title||'').slice(0,20)}`,
      title: raw.title || '',
      url: raw.url || '#',
      source: raw.source || domain || '',
      domain,
      tier: raw.source_tier || 2,
      published,
      summary: raw.summary || raw.content_summary || raw.content || '',
      tags: Array.isArray(raw.tags) ? raw.tags : [],
      evaluation,
      label: raw.label || '',
    };
  }

  function coerceArray(data){
    if(Array.isArray(data)) return data;
    if (data && typeof data==='object'){
      const arr=[];
      if (data.highlight && typeof data.highlight==='object') arr.push(data.highlight);
      if (data.categories && typeof data.categories==='object'){
        Object.values(data.categories).forEach(v=>{ if(Array.isArray(v)) arr.push(...v); });
      }
      if (arr.length) return arr;
    }
    return [];
  }

  function sortArticles(a,b){
    const la=labelPriority.indexOf(getLabel(a,state.persona));
    const lb=labelPriority.indexOf(getLabel(b,state.persona));
    if(la!==lb) return la-lb;
    if((a.tier||9)!==(b.tier||9)) return (a.tier||9)-(b.tier||9);
    const sa=getScore(a,state.persona), sb=getScore(b,state.persona);
    if(sa!==sb) return sb-sa;
    const ta=new Date(a.published||0).getTime(), tb=new Date(b.published||0).getTime();
    return tb-ta;
  }

  function renderCounts(list){ const counts={all:list.length,x:0,must_read:0,recommended:0,consider:0,skip:0}; list.forEach(a=>counts[getLabel(a,state.persona)]++); Object.keys(counts).forEach(k=>{ const el=document.querySelector(`[data-count="${k}"]`); if(el) el.textContent=counts[k]; }); const total=$('#p-count'); if(total) total.textContent=`${list.length}件`; }

  function cardHTML(a){
    const label=getLabel(a,state.persona);
    const labelClass=label==='x'?'p-label-x':label==='must_read'?'p-label-must':label==='recommended'?'p-label-rec':label==='skip'?'p-label-skip':'p-label-con';
    const score=getScore(a,state.persona);
    const tierClass=a.tier===1?'p-badge-tier1':'p-badge-tier2';
    const sum=(a.summary||'').trim(); const summary=sum.length>220?`${sum.slice(0,220)}…`:sum;
    return `
      <article class="p-card" data-id="${a.id}" data-label="${label}" data-tier="${a.tier}" data-score="${score}">
        <div class="p-card-header">
          <span class="p-label-pill ${labelClass}">${labelText[label]||label}</span>
          ${a.tier?`<span class="p-badge ${tierClass}">${a.tier===1?'高信頼':'一般'}</span>`:''}
        </div>
        <h3><a class="p-title-link" href="${a.url}" target="_blank" rel="noopener noreferrer">${escapeHtml(a.title)}</a></h3>
        <div class="p-meta">
          ${a.domain?`<img class="p-favicon" src="${faviconUrl(a.domain)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">`:''}
          <span class="p-source">${escapeHtml(a.domain||a.source||'')}</span>
          <span class="p-sep">•</span>
          <time class="p-date" datetime="${a.published}">${formatRelative(a.published)}</time>
        </div>
        ${summary?`<p class="p-summary">${escapeHtml(summary)}</p>`:''}
        <div class="p-scores">
          <div class="p-score-val" aria-label="総合スコア">${score}</div>
          <div class="p-score-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${score}"><div class="p-score-fill" style="width:${score}%"></div></div>
        </div>
        ${Array.isArray(a.tags)&&a.tags.length?`<div class="p-tags">${a.tags.slice(0,6).map(t=>`<span class="p-tag">${escapeHtml(t)}</span>`).join('')}</div>`:''}
      </article>`;
  }

  function applyFilters(){
    const term=state.search.trim().toLowerCase(); const tier=state.tier; const min=state.minScore; const label=state.activeLabel;
    filtered = allArticles.filter(a=>{
      if(label!=='all' && getLabel(a,state.persona)!==label) return false;
      if(tier!=='all' && String(a.tier)!==String(tier)) return false;
      if(getScore(a,state.persona) < min) return false;
      if(term){ const txt=`${a.title}\n${a.summary}`.toLowerCase(); if(!txt.includes(term)) return false; }
      return true;
    }).sort(sortArticles);
    render();
  }

  function render(){
    const list=$('#p-list'), empty=$('#p-empty'); if(!list||!empty) return; list.setAttribute('aria-busy','true'); list.innerHTML=filtered.map(cardHTML).join(''); list.removeAttribute('aria-busy'); empty.hidden = filtered.length!==0; renderCounts(allArticles);
  }

  function bindUI(){
    $$('.p-btn-toggle').forEach(btn=>btn.addEventListener('click',()=>{ const p=btn.dataset.persona; if(state.persona===p) return; state.persona=p; $$('.p-btn-toggle').forEach(b=>b.classList.toggle('is-active',b===btn)); applyFilters(); }));
    $$('.p-chip').forEach(chip=>chip.addEventListener('click',()=>{ state.activeLabel=chip.dataset.label||'all'; $$('.p-chip').forEach(c=>c.classList.toggle('is-active',c===chip)); applyFilters(); }));
    const tier=$('#p-tier'); if(tier) tier.addEventListener('change',()=>{ state.tier=tier.value; applyFilters(); });
    const q=$('#p-search'); if(q) q.addEventListener('input',()=>{ state.search=q.value||''; applyFilters(); });
    const r=$('#p-minscore'), rv=$('#p-minscore-val'); if(r&&rv){ const upd=()=>{ state.minScore=Number(r.value||0); rv.value=String(state.minScore); applyFilters(); }; r.addEventListener('input',upd); upd(); }
  }

  async function tryFetch(path){ try{ const res=await fetch(path,{cache:'no-store'}); if(!res.ok) return null; return await res.json(); } catch(e){ return null; } }

  async function load(){
    // Try multiple data sources (relative first, then absolute fallbacks)
    const candidates = [
      '../data/news.generated.json',
      '../data/latest.json',
      '../data/news.json',
      '../data/news.enriched.json',
      // absolute fallbacks in case of path/baseurl issues or cache delays
      'https://awano27.github.io/ai-news-site/docs/data/news.generated.json',
      'https://awano27.github.io/ai-news-site/docs/data/latest.json',
      'https://awano27.github.io/new-ai-news-site/data/news.generated.json'
    ];
    let data=null;
    for (const p of candidates){ data = await tryFetch(p); if (data) { break; } }
    const items = coerceArray(data);
    allArticles = items.map(normalizeItem);
    bindUI();
    applyFilters();
  }

  document.addEventListener('DOMContentLoaded', load);
})();
