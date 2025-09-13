// presentations/assets/presentations.js
// Nav state + recent slides list (UTF-8 safe)
(function(){
  const bySel = (sel, root=document) => root.querySelector(sel);
  const bySelAll = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function setActiveNav(){
    const here = location.pathname.split('/').pop() || 'index.html';
    bySelAll('.ntt-link').forEach(a => {
      try {
        const t = a.getAttribute('href') || '';
        const file = t.split('/').pop();
        if (file === here) a.setAttribute('aria-current','page');
      } catch(_){}
    });
  }

  function h32(str){ let h=2166136261>>>0; for(let i=0;i<str.length;i++){ h^=str.charCodeAt(i); h=Math.imul(h,16777619);} return h>>>0; }
  function pal(key){ const hh=h32(key)%360; const h2=(hh+40+(key.length%30))%360; return [ `hsl(${hh} 75% 58%)`, `hsl(${h2} 72% 54%)` ]; }
  function esc(s){ return (s||'').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  function makeThumb(title,w=320,h=180){ const [c1,c2]=pal(title||'Slide'); const t=esc((title||'').slice(0,22));
    const svg = `<?xml version='1.0' encoding='UTF-8'?>`
      +`<svg xmlns='http://www.w3.org/2000/svg' width='${w}' height='${h}' viewBox='0 0 ${w} ${h}'>`
      +`<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='${c1}'/><stop offset='100%' stop-color='${c2}'/></linearGradient></defs>`
      +`<rect width='${w}' height='${h}' rx='14' fill='url(#g)'/>`
      +`<text x='18' y='${Math.round(h*0.62)}' font-family='Inter,Segoe UI,Arial,sans-serif' font-weight='900' font-size='${Math.max(16,Math.round(w*0.08))}' fill='rgba(255,255,255,0.96)'>${t}</text>`
      +`</svg>`; return 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent(svg);
  }

  async function renderRecentSlides(){
    const host = bySel('#recent-slides'); if (!host) return;
    try {
      const res = await fetch('day_slides_index.html', { credentials: 'omit' });
      if (!res.ok) throw new Error('index fetch failed');
      const html = await res.text();
      const d = document.implementation.createHTMLDocument('slides');
      d.documentElement.innerHTML = html;
      const links = bySelAll('ul.slides a', d);

      const looksMojibake = (s) => /\uFFFD|\?|朁E|蟷|譛|譌|E\/[a-z]/i.test(s||'');

      const items = links.map(a => {
        const href = a.getAttribute('href') || '';
        const dateEl = a.querySelector('.date');
        const dateLabel = (dateEl ? dateEl.textContent : '').trim();
        const fullText = (a.textContent||'').trim();
        const text = dateLabel ? fullText.replace(dateLabel,'').trim() : fullText;
        const m = /day_slide_(\d{4})_(\d{2})_(\d{2})/.exec(href);
        const date = m ? `${m[1]}-${m[2]}-${m[3]}` : '';
        const fallbackTitle = dateLabel ? `${dateLabel} - Daily Slide` : 'Daily Slide';
        const title = (looksMojibake(text) || text.length < 2) ? fallbackTitle : text;
        return { href, title, date, dateLabel, ts: m ? Date.parse(`${m[1]}-${m[2]}-${m[3]}T00:00:00Z`) : 0 };
      }).filter(x => x.href).sort((a,b)=> b.ts - a.ts).slice(0, 8);

      const frag = document.createDocumentFragment();
      items.forEach(it => {
        const a = document.createElement('a');
        a.className = 'ntt-slide';
        a.href = it.href;
        a.innerHTML = `
          <img class="ntt-slide-thumb" alt="" loading="lazy" referrerpolicy="no-referrer" src="${makeThumb(it.title||it.date)}"/>
          <div>
            <span class="ntt-badge">${esc(it.dateLabel||'最新')}</span>
            <div class="ntt-slide-title">${esc(it.title||'Daily Slide')}</div>
            <div class="ntt-slide-meta">日次AIニュースダイジェスト</div>
          </div>`;
        frag.appendChild(a);
      });
      host.replaceChildren(frag);
    } catch (e){
      host.innerHTML = '<div class="ntt-card">Failed to load recent slides. <a class="ntt-inline" href="day_slides_index.html">Open list</a></div>';
    }
  }

  function init(){ setActiveNav(); renderRecentSlides(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once:true });
  else init();
})();
