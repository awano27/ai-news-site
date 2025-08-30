<script>
    // タブ切り替え機能
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(btn => btn.addEventListener('click', () => {
      tabs.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
      btn.classList.add('active'); btn.setAttribute('aria-selected','true');
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
      const target = document.querySelector(btn.dataset.target);
      if (target) target.classList.remove('hidden');
    }));

    // フィルタ・ソート機能
    const searchBox = document.getElementById('searchBox');
    const importanceFilter = document.getElementById('importanceFilter');
    const sortSelect = document.getElementById('sortSelect');

    function getVisibleCards() {
      const activeTab = document.querySelector('.tab.active');
      if (!activeTab) return [];
      const targetPanel = document.querySelector(activeTab.dataset.target);
      return targetPanel ? Array.from(targetPanel.querySelectorAll('.card')) : [];
    }

    function filterAndSortCards() {
      const query = searchBox ? searchBox.value.toLowerCase() : '';
      const importanceThreshold = importanceFilter ? parseInt(importanceFilter.value) : 0;
      const sortBy = sortSelect ? sortSelect.value : 'importance';

      const cards = getVisibleCards();

      cards.forEach(card => {
        // テキスト検索
        const titleEl = card.querySelector('.card-title');
        const summaryEl = card.querySelector('.card-summary');
        const sourceEl = card.querySelector('.chip');
        const title = titleEl ? titleEl.textContent.toLowerCase() : '';
        const summary = summaryEl ? summaryEl.textContent.toLowerCase() : '';
        const source = sourceEl ? sourceEl.textContent.toLowerCase() : '';

        const textMatch = !query || title.includes(query) || summary.includes(query) || source.includes(query);

        // 重要度フィルタ
        const importance = parseInt(card.dataset.importance || '50');
        const importanceMatch = importance >= importanceThreshold;

        // 表示・非表示
        if (textMatch && importanceMatch) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });

      // ソート
      if (sortBy !== 'none') {
        const container = cards[0]?.parentElement;
        if (container) {
          const visibleCards = cards.filter(card => card.style.display !== 'none');
          visibleCards.sort((a, b) => {
            switch (sortBy) {
              case 'importance':
                return parseInt(b.dataset.importance || '0') - parseInt(a.dataset.importance || '0');
              case 'freshness':
                return parseInt(b.dataset.freshness || '0') - parseInt(a.dataset.freshness || '0');
              case 'time':
                const timeA = new Date(a.querySelector('.time-ago')?.dataset.timestamp || '2023-01-01');
                const timeB = new Date(b.querySelector('.time-ago')?.dataset.timestamp || '2023-01-01');
                return timeB - timeA;
              default:
                return 0;
            }
          });

          visibleCards.forEach(card => container.appendChild(card));
        }
      }
    }

    // イベントリスナー設定
    if (searchBox) {
      searchBox.addEventListener('input', filterAndSortCards);
    }

    // フィルタ・ソートUIを動的に追加
    document.addEventListener('DOMContentLoaded', function() {
      const searchContainer = document.querySelector('.search-container');
      if (searchContainer) {
        searchContainer.innerHTML += `
          <div class="filter-controls">
            <select id="importanceFilter" title="重要度フィルター">
              <option value="0">全重要度</option>
              <option value="90">?? 最高重要度のみ</option>
              <option value="75">? 高重要度以上</option>
              <option value="50">?? 中重要度以上</option>
            </select>
            <select id="sortSelect" title="ソート順">
              <option value="importance">重要度順</option>
              <option value="freshness">鮮度順</option>
              <option value="time">時間順</option>
              <option value="none">ソートなし</option>
            </select>
          </div>
        `;

        // 新しいコントロールのイベントリスナー
        const importanceFilter = document.getElementById('importanceFilter');
        const sortSelect = document.getElementById('sortSelect');

        if (importanceFilter) importanceFilter.addEventListener('change', filterAndSortCards);
        if (sortSelect) sortSelect.addEventListener('change', filterAndSortCards);
      }

      // 初期ソート実行
      setTimeout(filterAndSortCards, 100);
    });
  </script>

