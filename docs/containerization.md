# Running Microcontact in containers

The Compose setup builds the frontend assets and runs Django's development server at <http://127.0.0.1:8000/> for local/development use.
The app uses PostgreSQL 18, matching production, in a separate `db` service.
The database and uploaded recordings are stored in the named volumes `pgdata`
and `media`.

## Requirements and startup

Use rootless Podman with the Docker Compose provider, or Docker with Compose.

From the repository root:

```sh
cp .env.example .env
# Edit .env and set DJANGO_SECRET_KEY, GMAPIKEY and DJANGO_DB_PASSWORD.
podman compose build
podman compose up -d
podman compose logs -f app
```

For Docker, replace `podman compose` with `docker compose`.

The app waits until the database is healthy, then applies migrations before
starting. The database port is not published on the host. The `DJANGO_DB_*`
values are only used to initialize an empty `pgdata` volume; changing them
later does not change the existing database role. To open a database shell:

```sh
podman compose exec db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

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

The database and generated audio are stored in the `pgdata` and `media` volumes.
To start over with an empty database and media, remove both volumes:

```sh
podman compose down --volumes
```

## Python tests

The test suite runs inside the app container against the PostgreSQL service.
pytest-django creates and removes a separate `test_<name>` database, so the
database role needs permission to create databases (the Compose role does):

```sh
podman compose exec app python -m pytest -q
```

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
