const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
  const url = 'file://' + path.resolve('presentations/recommended_tools.html');

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);

    // Repro path: open search suggestions then click filter.
    await page.fill('#searchInput', 'Notion');
    await page.waitForTimeout(400);
    await page.click('.filter-btn[data-filter="meeting"]');
    await page.waitForTimeout(400);

    const activeFilter = await page.$eval('.filter-btn.active', el => el.dataset.filter);
    assert.equal(activeFilter, 'meeting', 'meeting filter should become active');

    const meetingCheck = await page.$$eval('.tool-card', cards => {
      const visible = cards.filter(c => getComputedStyle(c).display !== 'none' && c.offsetParent !== null);
      const invalid = visible.filter(c => !(c.dataset.tags || '').split(',').includes('meeting'));
      return { visibleCount: visible.length, invalidCount: invalid.length };
    });

    assert.ok(meetingCheck.visibleCount > 0, 'meeting filter should show at least one tool');
    assert.equal(meetingCheck.invalidCount, 0, 'all visible cards should include meeting tag');

    // Reset should clear search and return all-filter state.
    await page.click('#uxResetBtn');
    await page.waitForTimeout(300);

    const afterReset = await page.evaluate(() => ({
      q: document.getElementById('searchInput')?.value || '',
      active: document.querySelector('.filter-btn.active')?.dataset.filter || '',
      visibleCount: Array.from(document.querySelectorAll('.tool-card'))
        .filter(el => getComputedStyle(el).display !== 'none' && el.offsetParent !== null).length
    }));

    assert.equal(afterReset.q, '', 'reset should clear search query');
    assert.equal(afterReset.active, 'all', 'reset should restore all filter');
    assert.ok(afterReset.visibleCount > 0, 'after reset there should be visible cards');

    console.log('PASS recommended_tools.e2e');
  } finally {
    await browser.close();
  }
})().catch((err) => {
  console.error('FAIL recommended_tools.e2e');
  console.error(err.stack || err.message || err);
  process.exit(1);
});
