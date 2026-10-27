const { test: base, expect } = require('@playwright/test');

const demoPlaces = {
  'buenos-aires': 'Buenos Aires',
  'sao-paulo': 'São Paulo',
  toronto: 'Toronto',
  montreal: 'Montréal',
  'new-york': 'New York',
  naples: 'Napoli',
  siena: 'Siena',
  'caxias-do-sul': 'Caxias do Sul',
};
const publicCities = Object.entries(demoPlaces)
  .filter(([slug]) => slug !== 'caxias-do-sul')
  .map(([, name]) => name);

// Keep errors useful without copying a Maps key from an error URL into logs.
const redact = text => text.replace(/([?&]key=)[^&\s]+/gi, '$1[redacted]');

const test = base.extend({
  browserErrors: [async ({ page }, use, testInfo) => {
    const errors = [];
    page.on('pageerror', error => errors.push(redact(error.message)));
    page.on('console', message => {
      // The development page also tries an optional livereload server. Its
      // connection failure is unrelated to these workflows. Maps auth/quota
      // failures, however, should be explicit even if the map shell renders.
      if (/Google Maps JavaScript API error:/.test(message.text())) {
        errors.push(redact(message.text()));
      }
    });
    await use();
    if (errors.length) {
      await testInfo.attach('browser-errors', {
        body: errors.join('\n'), contentType: 'text/plain',
      });
    }
    expect(errors, 'Uncaught browser errors or Google Maps API errors').toEqual([]);
  }, { auto: true }],
});

test.beforeAll(async ({ request }) => {
  const response = await request.get('/api/places/');
  expect(response.ok(), 'E2E_BASE_URL must point to the running Microcontact app').toBeTruthy();
  const places = await response.json();
  expect(Array.isArray(places), 'Expected the Microcontact places API').toBeTruthy();
  for (const [slug, name] of Object.entries(demoPlaces)) {
    const matches = places.filter(place => place.placeID === `microcontact-demo-v1-${slug}`);
    expect(matches, `Run python manage.py seed_demo_data first: missing demo ${name}`).toHaveLength(1);
    expect(matches[0].name).toBe(name);
  }
});

async function openContributions(page) {
  await page.goto('/#contributions', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveTitle('Microcontact');
  await expect(page.getByRole('region', { name: 'Map', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Search by place' })).toBeVisible();
  // Positive markers establish that the contribution data has rendered before
  // any assertions about absent markers are made.
  for (const name of publicCities) {
    await expect(page.getByRole('button', { name, exact: true })).toBeVisible();
  }
}

test('map navigation switches to participation and back', async ({ page }) => {
  await openContributions(page);
  await page.getByRole('tab', { name: 'Participate', exact: true }).click();
  await expect(page).toHaveURL(/#participate$/);
  await expect(page.getByRole('heading', { name: 'Choose your country' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Canada', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Search by place' })).toHaveCount(0);

  await page.getByRole('tab', { name: 'Show recordings', exact: true }).click();
  await expect(page).toHaveURL(/#contributions$/);
  await expect(page.getByRole('region', { name: 'Map', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Choose your country' })).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Search by place' })).toBeVisible();
  await page.getByRole('button', { name: 'Buenos Aires', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Buenos Aires', exact: true })).toBeVisible();
});

test('Buenos Aires shows three dialects, speaker details and playable audio', async ({ page }) => {
  await openContributions(page);
  await page.getByRole('button', { name: 'Buenos Aires', exact: true }).click();
  const recordings = page.locator('.contributions-pin');
  await expect(recordings.getByRole('heading', { level: 3 })).toHaveCount(3);
  for (const name of ['Neapolitan', 'Piedmontese', 'Salentino']) {
    await expect(recordings.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  await expect(recordings.locator('audio')).toHaveCount(3);
  const neapolitan = recordings.locator('.dialect').filter({
    has: page.getByRole('heading', { name: 'Neapolitan', exact: true }),
  });
  await neapolitan.getByRole('button', { name: 'Show details', exact: true }).click();
  const details = page.locator('.popover');
  await expect(details).toBeVisible();
  for (const text of [
    'rosa-buenos-aires (synthetic audio)', 'Age: 66 – 70',
    'Place of origin: Caserta, CE', 'Migrated in: 1956', 'Italian, Spanish',
  ]) {
    await expect(details).toContainText(text);
  }

  // Use the visible player button. Reading currentTime verifies decoded media
  // actually plays; a successful media request alone would not establish that.
  await neapolitan.getByRole('button', { name: 'Play', exact: true }).click();
  const audio = neapolitan.locator('audio');
  await expect.poll(() => audio.evaluate(element => element.currentTime), {
    message: 'The seeded MP3 should advance after clicking Play',
  }).toBeGreaterThan(0.1);
  expect(await audio.evaluate(element => element.error)).toBeNull();
});

test('public demo markers appear and private-only Caxias do Sul stays absent', async ({ page }) => {
  await openContributions(page);
  for (const name of publicCities) {
    await expect(page.getByRole('button', { name, exact: true })).toHaveCount(1);
  }
  await expect(page.getByRole('button', { name: 'Caxias do Sul', exact: true })).toHaveCount(0);

  // Toronto also has a private pending recording: only its two public
  // contributions should reach the browser's recording list.
  await page.getByRole('button', { name: 'Toronto', exact: true }).click();
  const recordings = page.locator('.contributions-pin');
  await expect(recordings.getByRole('heading', { name: 'Toronto', exact: true })).toBeVisible();
  await expect(recordings.locator('audio')).toHaveCount(2);
  await expect(recordings.getByRole('heading', { level: 3 })).toHaveCount(2);
  for (const name of ['Abruzzese/Teatino', 'Neapolitan']) {
    await expect(recordings.getByRole('heading', { name, exact: true })).toBeVisible();
  }
});

test('country and city selection opens an upload form for Toronto, Canada', async ({ page }) => {
  await page.goto('/#participate', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: 'Choose your country' })).toBeVisible();
  await page.getByRole('link', { name: 'Canada', exact: true }).click();
  await expect(page).toHaveURL(/#participate\/CA$/);
  const search = page.locator('#particip-query');
  await expect(search).toBeVisible();
  // Google Places listens to keyboard events. Select by city/province/country,
  // not suggestion order (there is also a Toronto in Prince Edward Island).
  await search.pressSequentially('Toronto', { delay: 80 });
  const toronto = page.locator('.pac-item').filter({ hasText: /Toronto\s*ON, Canada/ });
  await expect(toronto).toBeVisible();
  await toronto.click();

  await expect(page).toHaveURL(/#participate\/CA\/Toronto$/);
  await expect(page.getByRole('heading', { name: 'Toronto, Canada', exact: true })).toBeVisible();
  const form = page.locator('form').filter({ has: page.locator('#upload-file') });
  await expect(form.locator('#upload-file')).toBeVisible();
  await expect(form.locator('[name="place.name"]')).toHaveValue('Toronto');
  await expect(form.locator('[name="place.country"]')).toHaveValue('CA');
  await expect(form.locator('[name="place.placeID"]')).not.toHaveValue('');
  const latitude = Number(await form.locator('[name="place.latitude"]').inputValue());
  const longitude = Number(await form.locator('[name="place.longitude"]').inputValue());
  expect(latitude).toBeGreaterThan(43);
  expect(latitude).toBeLessThan(44);
  expect(longitude).toBeGreaterThan(-80);
  expect(longitude).toBeLessThan(-79);
  await expect(form.getByRole('button', { name: 'Submit', exact: true })).toBeEnabled();
  // Stop before submitting: these four smoke tests do not modify application data.
});
