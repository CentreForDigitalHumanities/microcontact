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

## Process handling

The image declares `STOPSIGNAL SIGINT` to use Django's `KeyboardInterrupt` exit path.
