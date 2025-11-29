const { test, expect } = require('@playwright/test');

test('slides index page screenshot', async ({ page }) => {
  // Get the absolute path to the local HTML file
  const path = require('path');
  const filePath = path.resolve(__dirname, '..', 'daily_slides_index.html');
  const fileUrl = 'file://' + filePath;

  await page.goto(fileUrl);

  // Wait for any potential animations or dynamic content to load
  await page.waitForTimeout(1000);

  await page.screenshot();
});
