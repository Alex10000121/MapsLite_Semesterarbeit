// @ts-check
import { test, expect } from '@playwright/test';

test('UI has inputs and shows top list', async ({ page }) => {
  await page.goto('http://localhost:5500/public/index.html');
  await expect(page.getByLabel('Von')).toBeVisible();
  await expect(page.getByLabel('Nach')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Route' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Top 10 Suchanfragen' })).toBeVisible();
});
