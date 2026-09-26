#!/bin/sh

attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge 30 ]; then
    echo "Database did not become ready after $attempt attempts" >&2
    exit 1
  fi
  echo "Database is not ready yet; retrying migration ($attempt/30)..."
  attempt=$((attempt + 1))
  sleep 2
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
