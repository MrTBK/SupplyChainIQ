-- 009_roles.sql — PROD Postgres only (not run on SQLite demo).
-- Run as superuser after init.
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='sci_loader') THEN CREATE ROLE sci_loader LOGIN PASSWORD 'change_me'; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='sci_analyst') THEN CREATE ROLE sci_analyst LOGIN PASSWORD 'change_me'; END IF;
END $$;
GRANT CONNECT ON DATABASE supplychainiq TO sci_analyst;
GRANT USAGE ON SCHEMA public TO sci_loader, sci_analyst;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO sci_loader;
GRANT SELECT ON mart_inventory, mart_procurement, mart_logistics, mart_demand, mart_risk TO sci_analyst;
REVOKE CREATE ON SCHEMA public FROM sci_analyst;
