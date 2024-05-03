#!/bin/bash

# Enable PostGIS extension in the specified database
psql -U postgres -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
psql -U postgres -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "PostGIS extensions enabled in database '$POSTGRES_DB'."

