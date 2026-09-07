#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
    uv run --no-sync alembic upgrade head
    exec uv run --no-sync telegram-message-trigger
else
    exec "$@"
fi
