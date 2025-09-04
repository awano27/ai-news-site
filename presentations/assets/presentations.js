// presentations/assets/presentations.js
// Minimal JS to support nav state and recent slides auto-list.
(function(){
  function bySel(sel, root=document){ return root.querySelector(sel); }
  function bySelAll(sel, root=document){ return Array.from(root.querySelectorAll(sel)); }

  // Highlight current nav item
  function setActiveNav(){
    const here = location.pathname.split('/').pop() || 'index.html';
    bySelAll('.ntt-link').forEach(a => {
      try { const t = a.getAttribute('href') || ''; const file = t.split('/').pop();
        if (file === here) a.setAttribute('aria-current','page');
      } catch(_){}
    });
  }

  // Basic hash for color pair generation
  function h32(str){ let h = 2166136261>>>0; for (let i=0;i<str.length;i++){ h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h>>>0; }
  function pal(key){ const hh=h32(key)%360; const h2=(hh+40+(key.length%30))%360; return [ `hsl(${hh} 75% 58%)`, `hsl(${h2} 72% 54%)` ]; }
  function esc(s){ return (s||'').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  // Heuristic detection of mojibake in text fetched from index
  function looksMojibake(s){
    if (!s) return false;
    return /\uFFFD/.test(s)       // Unicode replacement char
        || s.includes('朁E')      // artifact observed in repo
        || /[^\x00-\x7F]E/.test(s) // stray ASCII 'E' after multibyte
        || /E\/[a-z]/i.test(s)    // fragments like 'E/h3>'
        || /�/.test(s);
  }
  function makeThumb(title,w=320,h=180){ const [c1,c2]=pal(title||'Slide'); const t=esc((title||'').slice(0,22));
    const svg = `<?xml version='1.0' encoding='UTF-8'?>`
      +`<svg xmlns='http://www.w3.org/2000/svg' width='${w}' height='${h}' viewBox='0 0 ${w} ${h}'>`
      +`<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='${c1}'/><stop offset='100%' stop-color='${c2}'/></linearGradient></defs>`
      +`<rect width='${w}' height='${h}' rx='14' fill='url(#g)'/>`
      +`<text x='18' y='${Math.round(h*0.62)}' font-family='Inter,Segoe UI,Arial,sans-serif' font-weight='900' font-size='${Math.max(16,Math.round(w*0.08))}' fill='rgba(255,255,255,0.96)'>${t}</text>`
      +`</svg>`;
    return 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent(svg);
  }

  // Fetch and render recent daily slides from the day_slides_index.html
  async function renderRecentSlides(){
    const host = bySel('#recent-slides');
    if (!host) return;
    try {
      const res = await fetch('day_slides_index.html', { credentials: 'omit' });
      if (!res.ok) throw new Error('index fetch failed');
      const html = await res.text();
      const d = document.implementation.createHTMLDocument('slides');
      d.documentElement.innerHTML = html;
      const links = bySelAll('a[href*="day_slides/day_slide_"], a[href*="day_slides\\/day_slide_"]', d);
      const items = links.map(a => {
        const href = a.getAttribute('href');
        const text = (a.textContent||'').trim();
        const m = /day_slide_(\d{4})_(\d{2})_(\d{2})/.exec(href||'');
        const date = m ? `${m[1]}-${m[2]}-${m[3]}` : '';
        return { href, text, date, ts: m ? Date.parse(`${m[1]}-${m[2]}-${m[3]}T00:00:00Z`) : 0 };
      }).filter(x => x.href).sort((a,b)=> b.ts - a.ts).slice(0, 8);

      // Build cards
      const frag = document.createDocumentFragment();
      items.forEach(it => {
        const safeTitle = looksMojibake(it.text) ? '日別スライド' : it.text;
        const a = document.createElement('a');
        a.className = 'ntt-slide';
        a.href = it.href;
        a.innerHTML = `
          <img class="ntt-slide-thumb" alt="" loading="lazy" referrerpolicy="no-referrer" src="${makeThumb(safeTitle||it.date)}"/>
          <div>
            <span class="ntt-badge">${(it.date||'&#x6700;&#x65B0;')}</span>
            <div class="ntt-slide-title">${esc(safeTitle||'Daily Slide')}</div>
            <div class="ntt-slide-meta">&#x65E5;&#x5225;&#x30B9;&#x30E9;&#x30A4;&#x30C9;&#x30FB;&#x6700;&#x65B0;&#x306E;&#x30C0;&#x30A4;&#x30B8;&#x30A7;&#x30B9;&#x30C8;</div>
          </div>`;
        frag.appendChild(a);
      });
      host.replaceChildren(frag);
    } catch (e) {
      // Graceful fallback
      host.innerHTML = '<div class="ntt-card">&#x6700;&#x65B0;&#x30B9;&#x30E9;&#x30A4;&#x30C9;&#x306E;&#x53D6;&#x5F97;&#x306B;&#x5931;&#x6557;&#x3057;&#x307E;&#x3057;&#x305F;&#x3002;<a class="ntt-inline" href="day_slides_index.html">&#x4E00;&#x89A7;&#x3092;&#x898B;&#x308B;</a></div>';
    }
  }

  function init(){
    setActiveNav();
    renderRecentSlides();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once:true });
  } else { init(); }
})();
