FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV DJANGO_SETTINGS_MODULE=bm2.settings
ENV ALLOWED_HOSTS=bm2.brntn.me,localhost,127.0.0.1

RUN DJANGO_SECRET_KEY=build-only uv run python manage.py collectstatic --noinput

RUN useradd -m app && chown -R app /app
USER app

EXPOSE 8000

CMD uv run python manage.py migrate --noinput && uv run gunicorn bm2.wsgi:application --bind 0.0.0.0:8000
