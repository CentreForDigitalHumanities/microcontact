# syntax=docker/dockerfile:1
# Microcontact container image (rootless Podman / Docker Compose engine).
#
# Stage 1 builds the frontend assets with the Node version that the pinned
# node-sass 4.14 still supports. Stage 2 compiles Python wheels against the
# Debian 12 (bookworm) headers. Stage 3 is the non-root runtime image.

FROM docker.io/library/node:12-bullseye AS assets

WORKDIR /src

COPY package.json package-lock.json bower.json ./

RUN npm ci --no-audit --no-fund \
    && npm install --global bower@1.8.14

RUN bower install --allow-root --config.interactive=false --config.analytics=false

COPY Gruntfile.coffee ./
COPY grunt-tasks ./grunt-tasks
COPY client ./client

RUN ./node_modules/.bin/grunt compile

FROM docker.io/library/python:3.7-slim AS pybuild

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc libc6-dev libldap2-dev libsasl2-dev libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM docker.io/library/python:3.7-slim AS runtime

ARG APP_UID=1000
ARG APP_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Runtime libraries for python-ldap/pyldap, psycopg2 and python-magic, plus
# ffmpeg for the AMR/WAV -> MP3 conversion in recordings/convert_audio.py.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libldap-2.5-0 libsasl2-2 libpq5 libmagic1 ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid app --create-home app

WORKDIR /app

COPY requirements.txt ./
# Mount the wheels only for installation so the archives never enter an image layer.
RUN --mount=type=bind,from=pybuild,source=/wheels,target=/wheels \
    pip install --no-index --find-links=/wheels -r requirements.txt

COPY manage.py conftest.py ./
COPY microcontact ./microcontact
COPY recordings ./recordings
COPY container ./container

COPY --from=assets /src/.tmp ./.tmp
COPY --from=assets /src/bower_components ./bower_components

# grunt compile creates relative symlinks inside .tmp that point back into
# client/; keep those targets present in the runtime image.
COPY --chown=app:app client/image ./client/image
COPY --chown=app:app client/script/mock ./client/script/mock

RUN chmod +x /app/container/entrypoint.sh \
    && mkdir -p /data media \
    && touch /data/.keep \
    && chown -R app:app /app /data media

ENV DJANGO_SETTINGS_MODULE=microcontact.settings_container \
    DJANGO_DB_PATH=/data/db.sqlite3 \
    DJANGO_MEDIA_ROOT=/app/media \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

# Preserve Django's KeyboardInterrupt exit path when Compose's init forwards
# the stop signal. This also lets the server stop when run directly as PID 1.
STOPSIGNAL SIGINT

ENTRYPOINT ["/app/container/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
