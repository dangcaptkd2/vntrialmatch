#!/bin/bash

# Simple script to import AACT PostgreSQL dump into Docker container

DUMP_FILE="$1"
CONTAINER="postgres_db"
DB="aact"
USER="postgres"

if [ -z "$DUMP_FILE" ]; then
  echo "[ERROR] Please provide the path to the PostgreSQL dump file"
  echo "Usage: $0 path/to/postgres.dmp"
  exit 1
fi

if [ ! -f "$DUMP_FILE" ]; then
  echo "[ERROR] File not found: $DUMP_FILE"
  exit 1
fi

echo "[INFO] Checking if container '$CONTAINER' is running..."
if ! docker ps | grep -q "$CONTAINER"; then
  echo "[INFO] Starting container with docker-compose..."
  docker-compose up -d postgres
  sleep 10
fi

echo "[INFO] Dropping and creating database '$DB'..."
docker exec "$CONTAINER" psql -U "$USER" -c "DROP DATABASE IF EXISTS $DB;"
docker exec "$CONTAINER" psql -U "$USER" -c "CREATE DATABASE $DB;"

echo "[INFO] Copying dump file into container..."
docker cp "$DUMP_FILE" "$CONTAINER:/tmp/postgres.dmp"

echo "[INFO] Restoring database..."
docker exec "$CONTAINER" pg_restore -U "$USER" -d "$DB" --no-owner -v /tmp/postgres.dmp

echo "[INFO] Cleaning up..."
docker exec "$CONTAINER" rm /tmp/postgres.dmp

echo "[INFO] Done! You can now access the '$DB' database."
