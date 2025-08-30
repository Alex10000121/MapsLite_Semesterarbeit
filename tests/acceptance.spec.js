const { test, expect } = require('@playwright/test');

const FRONTEND = 'http://127.0.0.1:5500/public/index.html';
const BACKEND = 'http://127.0.0.1:8000';

test.describe('Akzeptanztest – LiteMaps', () => {
  test.setTimeout(90_000);

  test('UI lädt, Route wird berechnet, gespeichert, erneut angezeigt, persistiert und löschbar', async ({ page, request }) => {
    // Backend erreichbar
    const h = await request.get(`${BACKEND}/health`, { timeout: 15_000 });
    expect(h.status()).toBe(200);
    const j = await h.json();
    expect(j.status).toBe('ok');

    // UI laden
    await page.goto(FRONTEND, { waitUntil: 'domcontentloaded', timeout: 30_000 });

    // Grund-UI sichtbar
    await expect(page.getByRole('heading', { name: /^litemaps$/i })).toBeVisible();
    const von = page.getByLabel('Von');
    const nach = page.getByLabel('Nach');
    await expect(von).toBeVisible();
    await expect(nach).toBeVisible();
    const suche = page.getByRole('button', { name: /suche/i });
    await expect(suche).toBeVisible();

    // Eingaben
    const startText = 'Zürich HB, Schweiz';
    const zielText = 'Bern Bahnhof, Schweiz';
    await von.fill(startText);
    await nach.fill(zielText);

    // Suche auslösen und auf Speichern (POST /api/routes) warten
    const waitSaved = page.waitForResponse(
      r => r.url().endsWith('/api/routes') && r.request().method() === 'POST',
      { timeout: 60_000 }
    );
    await suche.click();
    const savedResp = await waitSaved;
    expect(savedResp.ok()).toBeTruthy();

    // Gespeicherte Liste enthält Eintrag
    const savedList = page.locator('#saved-list');
    await expect(savedList).toBeVisible();
    await expect(savedList).toContainText('Zürich HB, Schweiz');
    await expect(savedList).toContainText('Bern Bahnhof, Schweiz');

    // Anzeigen der Route -> Leaflet-Polyline sichtbar
    const anzeigenBtn = savedList.getByRole('button', { name: /anzeigen/i }).first();
    await anzeigenBtn.click();
    const polyline = page.locator('path.leaflet-interactive').first();
    await expect(polyline).toBeVisible({ timeout: 20_000 });

    // Persistenz: Seite neu laden -> Eintrag weiterhin vorhanden
    await page.reload({ waitUntil: 'domcontentloaded' });
    const savedListAfterReload = page.locator('#saved-list');
    await expect(savedListAfterReload).toContainText('Zürich HB, Schweiz');
    await expect(savedListAfterReload).toContainText('Bern Bahnhof, Schweiz');

    // Löschen: ersten passenden Eintrag löschen und das Verschwinden prüfen
    const loeschenBtn = savedListAfterReload.getByRole('button', { name: /löschen/i }).first();
    const waitDelete = page.waitForResponse(
      r => /\/api\/routes\/\d+$/.test(r.url()) && r.request().method() === 'DELETE',
      { timeout: 30_000 }
    );
    await loeschenBtn.click();
    await waitDelete;

    // Nach kurzer Wartezeit darf der konkrete Text nicht mehr vorhanden sein
    await expect(savedListAfterReload).not.toContainText(`${startText} → ${zielText}`, { timeout: 15_000 });
  });
});