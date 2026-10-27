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

These tests use a temporary database and media directory. They do not automate
the browser's Google Maps interactions. Public visibility here refers to API
listing/detail access; the existing media serving configuration does not enforce
recording visibility on a known file URL.
