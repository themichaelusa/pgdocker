#!/bin/bash

# Start PgBouncer
su - pgbouncer_user -c "/usr/sbin/pgbouncer -d /etc/pgbouncer/pgbouncer.ini"

# Call the original PostgreSQL entrypoint script
exec /usr/local/bin/docker-entrypoint.sh "$@"