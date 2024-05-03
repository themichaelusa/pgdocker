FROM postgres:16.2-bookworm

# Create a directory for the PostgreSQL data
RUN mkdir -p /var/lib/postgresql/data

# Install PostGIS dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts && \
    rm -rf /var/lib/apt/lists/*

# Install PGVector
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update && apt install -y postgresql-16-pgvector

# Install PGBouncer
RUN apt-get update && apt-get install -y pgbouncer

# Copy custom PostgreSQL configuration files (e.g. postgresql.conf, pg_hba.conf)
COPY conf/postgresql /etc/postgresql

# Create a non-root user for PgBouncer with a home directory && Set ownership and permissions for necessary directories
RUN groupadd -r pgbouncer && \
    useradd -r -g pgbouncer -m -d /home/pgbouncer_user pgbouncer_user && \
    mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer && \
    chown -R pgbouncer_user:pgbouncer /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer

# Copy custom PGBouncer configuration files (e.g. pgbouncer.ini, userlist.txt)
COPY --chown=pgbouncer_user:pgbouncer conf/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY --chown=pgbouncer_user:pgbouncer conf/pgbouncer/userlist.txt /etc/pgbouncer/userlist.txt

# Ensure pgbouncer_user can write to the log file
RUN touch /var/log/pgbouncer/pgbouncer.log && chown pgbouncer_user:pgbouncer /var/log/pgbouncer/pgbouncer.log

# Restart pgbouncer so it can pick up the new config
RUN service pgbouncer restart

# Expose the PGBouncer port (default: 6432, don't expose the PostgreSQL port)
EXPOSE 6432

# Copy and set permissions for the init_db.sh script
COPY scripts/init_db.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init_db.sh

# Copy the custom entrypoint script
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the new entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["postgres"]