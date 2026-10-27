# Running Microcontact in containers

The Compose setup builds the frontend assets and runs Django's development server at <http://127.0.0.1:8000/> for local/development use.
The app runs with SQLite and uploaded recordings stored in named volumes.

## Requirements and startup

Use rootless Podman with the Docker Compose provider, or Docker with Compose.

From the repository root:

```sh
cp .env.example .env
# Edit .env and set DJANGO_SECRET_KEY and GMAPIKEY.
podman compose build
podman compose up -d
podman compose logs -f app
```

For Docker, replace `podman compose` with `docker compose`.

Source files are baked into the image; after changing them, run:

```sh
podman compose up -d --build
```

To create an administrator in the running container:

```sh
podman compose exec app python manage.py createsuperuser
```

## Demo data

Populate the running local instance with fictional profiles and playable synthetic audio:

```sh
podman compose exec app python manage.py seed_demo_data
```

This adds 15 recordings (12 public, three private) at eight locations, reusing
the migrated reference data. It is safe to rerun: existing demo recordings and
moderation edits are kept. To recreate only the tagged demo recordings and
their audio:

```sh
podman compose exec app python manage.py seed_demo_data --reset
```

The database and generated audio persist in the existing `db` and `media` volumes.

## Browser tests

Run the separate Playwright package on the host against the running app's
published port. See [browser test setup](demo-data.md#browser-map-tests) for
installation and the four covered workflows. For an app on port 8002, after
installing the runner and Chromium:

```sh
cd e2e
E2E_BASE_URL=http://127.0.0.1:8002 npm test
```

The app container needs no test-runner dependencies or rebuild for these tests.

## Process handling

The image declares `STOPSIGNAL SIGINT` to use Django's `KeyboardInterrupt` exit path.
