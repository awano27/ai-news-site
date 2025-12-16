document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const filterContainer = document.getElementById('filterContainer');
    const toolCards = document.querySelectorAll('.tool-card');
    const noResults = document.getElementById('noResults');
    const scrollTopBtn = document.getElementById('scrollTopBtn');

    let currentFilter = 'all';

    function filterAndSearchTools() {
      const searchTerm = searchInput.value.toLowerCase();
      let hasResults = false;

      toolCards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const subtitle = card.querySelector('.tool-subtitle') ? card.querySelector('.tool-subtitle').textContent.toLowerCase() : '';
        const description = card.querySelector('.tool-description').textContent.toLowerCase();
        // Use classList for filtering based on category classes added to tool-card
        
        const cardText = title + ' ' + subtitle + ' ' + description; // Simplified cardText for search

        const matchesSearch = cardText.includes(searchTerm);
        const matchesFilter = currentFilter === 'all' || card.classList.contains(currentFilter); // Now checking card class

        if (matchesSearch && matchesFilter) {
          card.style.display = '';
          hasResults = true;
        } else {
          card.style.display = 'none';
        }
      });

      if (hasResults) {
        noResults.style.display = 'none';
      } else {
        noResults.style.display = 'block';
      }
    }

    searchInput.addEventListener('input', filterAndSearchTools);

    filterContainer.addEventListener('click', (event) => {
      if (event.target.classList.contains('filter-btn')) {
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        currentFilter = event.target.dataset.filter;
        filterAndSearchTools();
      }
    });
    
    // Initial filter when page loads
    filterAndSearchTools();

    // Scroll to top button logic
    window.addEventListener('scroll', () => {
      if (window.pageYOffset > 300) {
        scrollTopBtn.classList.add('visible');
      } else {
        scrollTopBtn.classList.remove('visible');
      }
    });

    scrollTopBtn.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  });
