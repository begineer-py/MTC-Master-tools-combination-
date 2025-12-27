#!/bin/bash
set -e 
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
CREATE USER myuser WITH PASSWORD 'secret';
CREATE DATABASE mydb OWNER myuser;
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
EOSQL
echo "Database setup complete"