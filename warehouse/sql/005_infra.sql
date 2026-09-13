-- 005_watermarks.sql + 006_etl_log.sql + 007_quarantine.sql

CREATE TABLE IF NOT EXISTS etl_watermark (
  source TEXT PRIMARY KEY,
  last_key TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etl_execution_log (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  source TEXT NOT NULL,
  rows_read INTEGER NOT NULL DEFAULT 0,
  rows_accepted INTEGER NOT NULL DEFAULT 0,
  rows_rejected INTEGER NOT NULL DEFAULT 0,
  errors TEXT DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'running',
  duration_s REAL
);

CREATE TABLE IF NOT EXISTS dq_quarantine (
  id INTEGER PRIMARY KEY,
  run_id TEXT NOT NULL,
  source TEXT NOT NULL,
  business_key TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_quarantine_run ON dq_quarantine(run_id);

CREATE TABLE IF NOT EXISTS dq_batch_score (
  run_id TEXT NOT NULL,
  source TEXT NOT NULL,
  rows_read INTEGER NOT NULL,
  rows_accepted INTEGER NOT NULL,
  score REAL NOT NULL,
  PRIMARY KEY (run_id, source)
);
