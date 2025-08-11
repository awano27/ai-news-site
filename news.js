// news.js
(async () => {
    const fetchJSON = async (url) => {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) throw new Error('failed:' + r.status);
      return r.json();
    };
    const data = await fetchJSON('news/latest.json').catch(() => null);
    if (!data) {
      const el = document.querySelector('.highlight-section');
      if (el) el.innerHTML = `<div class="highlight-card"><h2>本日の更新はまだありません</h2><p>しばらくしてから再読み込みしてください。</p></div>`;
      return;
    }
  
    const starStr = n => '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n);
    const esc = (s) => (s || '').replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\\':'\\'}[c]));
  
    // ハイライト
    const h = data.highlight || null;
    if (h) {
      const sources = (h.sources || [])
        .map(s => `<a class="source-link" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">出典: ${esc(s.name||'link')}</a>`)
        .join('');
      const el = document.querySelector('.highlight-section');
      if (el) el.innerHTML = `
        <div class="highlight-card">
          <span class="category">${esc(h.category||'')}</span>
          <span class="stars">${starStr(h.stars||0)}</span>
          <h2>${esc(h.title||'')}</h2>
          <p>${esc(h.summary||'')}</p>
          <div class="meta">${sources}</div>
        </div>`;
    }
  
    const renderCard = it => {
      const src = it.source || {};
      const date = it.date ? `<span>${esc(it.date)}</span>` : '';
      const link = src.url ? `<a class="source-link" href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">${src.name? '出典':'リンク'}</a>` : '';
      return `
        <article class="card">
          <span class="category">${esc(it.category||'')}</span>
          <span class="stars">${starStr(it.stars||0)}</span>
          <h3>${esc(it.title||'')}</h3>
          <p>${esc(it.blurb||'')}</p>
          <div class="meta">${date}${link}</div>
        </article>`;
    };
  
    const INITIAL_COUNT = 12;
    ['business','tools','company','sns'].forEach(id => {
      const list = document.querySelector(`#${id} .card-list`);
      if (!list) return;
      const items = (data.sections&&data.sections[id])? data.sections[id] : [];
      // データが無い場合は静的プレースホルダーを維持
      if (!items || items.length === 0) return;

      let shown = Math.min(INITIAL_COUNT, items.length);
      const renderSlice = () => {
        list.innerHTML = items.slice(0, shown).map(renderCard).join('');
      };
      renderSlice();

      // もっと見るボタン
      const container = document.getElementById(id);
      if (!container) return;
      let moreBtn = container.querySelector('.more-btn');
      if (!moreBtn && items.length > INITIAL_COUNT) {
        moreBtn = document.createElement('button');
        moreBtn.className = 'more-btn';
        moreBtn.textContent = 'もっと見る';
        moreBtn.setAttribute('aria-label', `${id} をさらに表示`);
        container.appendChild(moreBtn);
      }
      const updateBtn = () => {
        if (!moreBtn) return;
        if (shown >= items.length) {
          moreBtn.style.display = 'none';
        } else {
          moreBtn.style.display = '';
        }
      };
      updateBtn();
      if (moreBtn) {
        moreBtn.addEventListener('click', () => {
          shown = Math.min(items.length, shown + INITIAL_COUNT);
          renderSlice();
          updateBtn();
        });
      }
    });
  
    const f = document.querySelector('footer p');
    if (f && data.generated_at) {
      const ts = new Date(data.generated_at);
      f.textContent = `更新：${ts.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })} JST`;
    }
  })();