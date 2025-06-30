const { test, expect } = require('@playwright/test');

test('Formular ist sichtbar und nutzbar', async ({ page }) => {
  await page.goto('http://localhost:8000/frontend/index.html'); // oder WebStorm-URL einfügen

  await expect(page.locator('#start')).toBeVisible();
  await expect(page.locator('#ziel')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Suche' })).toBeVisible();

  await page.locator('#start').fill('Bern');
  await page.locator('#ziel').fill('Zürich');
  await page.getByRole('button', { name: 'Suche' }).click();
});

