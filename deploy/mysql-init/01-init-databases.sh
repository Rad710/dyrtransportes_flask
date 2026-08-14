#!/bin/bash
# Runs once, on first init of the mysql-shared data volume. Creates the per-app
# databases and users. Passwords come from the container environment (.env).
set -e

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
-- text-to-sql-rag: synthetic query DB + read-only user
CREATE DATABASE IF NOT EXISTS dyrtransportes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'llm_readonly'@'%' IDENTIFIED BY '${QUERY_DB_PASSWORD}';
GRANT SELECT ON dyrtransportes.* TO 'llm_readonly'@'%';

-- D y R Transportes demo: app DB + read/write user (needs DDL + triggers → ALL on its own DB)
CREATE DATABASE IF NOT EXISTS dyr_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'dyr'@'%' IDENTIFIED BY '${DYR_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON dyr_demo.* TO 'dyr'@'%';

FLUSH PRIVILEGES;
SQL

echo "shared MySQL: created databases dyrtransportes (read-only) and dyr_demo (read/write)."
