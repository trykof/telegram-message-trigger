# telegram-message-trigger

A Telegram bot that auto-replies to a business account's personal messages
based on trigger rules configured by the account owner, using the
[Telegram Business](https://core.telegram.org/bots/business) chatbot
integration.

See [CLAUDE.md](CLAUDE.md) for the full product concept and scope.

## Requirements

- Python 3.11
- [uv](https://docs.astral.sh/uv/)
- A bot token from [@BotFather](https://t.me/BotFather) with Business mode
  enabled

## Local development

```bash
uv sync
cp .env.example .env    # fill in BOT_TOKEN
```

> **Note:** if the repo lives under a path containing non-ASCII characters
> (e.g. a localized `OneDrive\Документы` folder on Windows), Python's `site`
> module fails to register the editable install (it reads `.pth` files using
> the OS locale encoding, not UTF-8, so the Cyrillic path gets mangled and
> silently dropped from `sys.path`). `uv sync` still works fine for managing
> dependencies, but `uv run telegram-message-trigger` / `uv run alembic` /
> `uv run pytest` won't find the local package. In that case, use Docker
> (below) to actually run and test the bot; `uv` locally is still useful for
> `ruff`/`mypy`/dependency management.

By default `DATABASE_URL` points at a local SQLite file, so no extra
services are needed for development where this isn't an issue.

## Running with Docker

```bash
cp .env.example .env    # fill in BOT_TOKEN
docker compose up --build
```

This starts the bot alongside a PostgreSQL database (`DATABASE_URL` is
overridden in `docker-compose.yml` to point at it).

## Migrations

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Tooling

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```
