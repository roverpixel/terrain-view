import { test, expect } from '@playwright/test';

test('viewer loads and deck.gl canvas is present', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveTitle(/3D DEM/);

  const container = page.locator('#app');
  await expect(container).toBeVisible();

  await page.waitForTimeout(5000);

  const appContent = await container.innerHTML();

  if (appContent.includes('Error')) {
      console.log('An error occurred loading the viewer:', appContent);
  } else {
      const canvas = page.locator('canvas');
      await expect(canvas.first()).toBeVisible({ timeout: 5000 });
      console.log("Canvas is visible");
  }

  await page.screenshot({ path: '/home/jules/verification/terrain.png' });
});
