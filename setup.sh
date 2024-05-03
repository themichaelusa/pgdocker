apt-get update

sudo apt install -y postgresql-common

/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

apt-get update

sudo apt-get install -y postgresql-client-16

# at this point we can do things like pg_dump and pg_restore if we so choose

# TODO: turn this the below into it's own migration script

CONNSTR = "postgresql://pguser:password@host:5432/dbname"

pg_dump -j 4 -Fd -d "$CONNSTR" -f "db_backup_dir" &

# Restore into table here
set PGPASSWORD="password" && pg_restore -v -h localhost -p 6432 -U postgres -d lake -j 4 --no-owner --role=postgres ./db_backup_dir/ > restore.log 2>&1