Demo data for testing
-------------------------------

To populate a local instance with fictional speakers and playable audio:

```sh
python manage.py migrate
python manage.py seed_demo_data
```

The command requires the existing audio dependency, `ffmpeg`. It creates 15
recordings at eight locations across Argentina, Brazil, Canada, Italy and the
USA, using the countries, dialects, languages and age categories installed by
migrations. All nine dialect categories occur in the public examples. The
profiles include first- and second-generation speakers, several education and
age groups, multilingual speakers, and uploads on a relative's behalf. Years
and ages describe fictional profiles from the research period around 2018.

There are 12 public recordings and three private ones: open/pending, reviewed
but unpublished, and censored. Seven locations appear as map markers; Caxias do
Sul has only a private recording and should have no marker. Buenos Aires has
three public dialects to exercise the pie marker and grouped recording list.

Audio consists of two-second synthetic tones, **not dialect speech**. Fourteen
WAV files go through the regular rename and MP3 conversion signals; one MP3
exercises direct playback without conversion. Names are prefixed with `Demo:`,
emails use `example.invalid`, and data-source labels start with
`Microcontact demo v1:`. No external data or Google requests are needed to seed.

Rerunning the command skips existing demo recordings, preserving IDs, media,
and edits made while testing moderation. To restore the original scenarios:

```sh
python manage.py seed_demo_data --reset
```

Reset deletes and recreates only recordings with the command's exact reserved
data-source labels, including their audio; recording IDs and URLs will change.
It retains places, reference lists, users and unrelated uploads. Keep the demo
data-source labels intact so the command can recognize its records. Demo place
IDs start with `microcontact-demo-v1-`; they are synthetic identifiers, not
Google Place IDs, so a subsequent Google-selected upload can create a separate
place for the same city.

### Model and workflow

| Model | Role |
| --- | --- |
| `Country` | Localized names and a unique country code; owns places. |
| `Place` | Name, coordinates and external place ID; groups recordings on the map. |
| `Dialect` | Localized names and marker color; each recording has one dialect. |
| `Language` | Localized names; recordings can have multiple languages. |
| `AgeCategory` | Inclusive age range referenced by each demo speaker. |
| `Recording` | Speaker/uploader metadata, moderation flags, original audio and optional MP3 derivative. |

The public API lists reference data and places, and accepts recordings with a
nested place and at least one contact method (email or phone). It reuses places
by `placeID`. New uploads are open and private. Django admin handles review and
publication. The `public` flag alone controls inclusion in `/api/recordings/`
and the recordings nested in `/api/places/`; changing `status` alone does not
publish or withdraw a recording. One demo recording is deliberately open and
public to expose this distinction. Uploader contact fields are omitted from
public responses; a separate admin permission controls their visibility.

### Manual walkthrough

1. Build/start the frontend as described below, seed, and create an admin with
   `python manage.py createsuperuser` if needed. Seeding does not create users.
2. Open `/#contributions`, select Buenos Aires, inspect the three dialect groups
   and speaker details, and play a recording. The browser map and location
   search still require a working Google Maps key.
3. Open `/admin/recordings/recording/` and search for `Demo:`. Filter for private,
   open recordings to find `pending-toronto`. Set it to reviewed and public.
   Reload the contributions page to see the additional Toronto recording.
4. Use `/#participate` to choose a country/city and submit an audio file with
   speaker details and a contact method. An original WAV from a demo recording's
   admin page can serve as the upload file. The new upload should be open and
   private; publish it in admin, reload the map, and check playback.
5. Clear `public` in admin and reload to check that the contribution disappears.
   Reset restores the tagged demo scenarios; manually submitted uploads remain.

The integration tests exercise seeding, repeat/reset behavior, real audio
conversion, API/media access, upload validation and admin publication:

```sh
DJANGO_SETTINGS_MODULE=microcontact.settings python -m pytest recordings/seed_demo_data_test.py
```

These Python tests use a temporary database and media directory. Public
visibility here refers to API listing/detail access; the existing media serving
configuration does not enforce recording visibility on a known file URL.

### Browser map tests

The separate `e2e/` package runs four Playwright tests in Chromium against a
running Microcontact instance and the real Google Maps/Places services:

1. Open the contributions map, switch to participation, and return to a working
   contributions map.
2. Click Buenos Aires, check its three dialect groups and speaker details, then
   click Play and verify the audio's playback time advances.
3. Check all seven public demo markers and the absence of private-only Caxias
   do Sul; Toronto must show only its two public recordings.
4. Choose Canada, type Toronto, select the Ontario autocomplete suggestion, and
   check the upload form's location and coordinates.

Use Node 22 or newer for this package. Its dependencies and lockfile are
independent of the application's legacy Node build. The app needs a working
Google Maps key with Places access for the hostname used by the browser.

Start the app and seed it first. For the Compose setup, from the repository root:

```sh
podman compose up -d
podman compose exec app python manage.py seed_demo_data
```

Install the browser runner separately:

```sh
cd e2e
npm ci
npx playwright install chromium
E2E_BASE_URL=http://127.0.0.1:8002 npm test
```

Set `E2E_BASE_URL` to the app's published address (match `APP_PORT` in `.env`).
Without this override the runner uses `http://127.0.0.1:8000`. It does not read
the app's `.env` or start/rebuild containers. On supported Linux distributions,
`npx playwright install --with-deps chromium` can also install browser system
dependencies. See [Playwright's installation guidance](https://playwright.dev/docs/intro).

Tests use fresh browser sessions, an English locale, one worker and no automatic
retries. They perform no uploads, moderation changes, seeding or resets. Existing
unrelated recordings are allowed; the demo scenarios must retain their original
names and publication states. If you edited those scenarios, explicitly restore
them with `seed_demo_data --reset` before running the tests. Missing demo places
produce a setup failure rather than skipped tests.

For a visible browser or the last run's HTML report, from `e2e/`:

```sh
E2E_BASE_URL=http://127.0.0.1:8002 npm run test:headed
npm run report
```

Failures retain screenshots and traces in `e2e/test-results/`; the report is in
`e2e/playwright-report/`. Both directories and the runner's dependencies are
ignored by Git and excluded from the app image build context. Uncaught browser
exceptions and Maps API errors fail the tests. The optional development
livereload server's connection error does not. These live integration tests
also depend on Google service availability, key configuration and network access.

The older CasperJS smoke test remains available through Grunt; this Playwright
suite is the browser regression baseline for dependency upgrades.
