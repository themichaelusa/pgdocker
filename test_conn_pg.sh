#!/bin/bash

# Set the connection details
# TODO: read from .env

# Test the connection
echo "Testing connection to PostgreSQL..."
if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\q" > /dev/null 2>&1; then
    echo "Connection successful!"
else
    echo "Connection failed. Please check the container logs for more information."
    exit 1
fi