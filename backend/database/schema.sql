-- SQL schema for initial database (Postgres / SQLite compatible)

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plans (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  answers_json JSON NOT NULL,
  answers_fingerprint TEXT NOT NULL,
  template_version TEXT NOT NULL,
  persona_label TEXT,
  overview_md TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS stages (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  stage_number INTEGER NOT NULL,
  title TEXT NOT NULL,
  is_free BOOLEAN NOT NULL DEFAULT 0,
  content_md TEXT NOT NULL,
  FOREIGN KEY (plan_id) REFERENCES plans(id)
);

CREATE TABLE IF NOT EXISTS entitlements (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  tier TEXT NOT NULL CHECK (tier IN ('free','pro')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES plans(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS verification_codes (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  code TEXT NOT NULL,
  code_type TEXT NOT NULL CHECK (code_type IN ('login','unlock')),
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rate_limits (
  id TEXT PRIMARY KEY,
  email TEXT,
  ip TEXT,
  endpoint TEXT NOT NULL,
  event_type TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster lookup
CREATE INDEX IF NOT EXISTS idx_plans_fingerprint ON plans (answers_fingerprint);
CREATE INDEX IF NOT EXISTS idx_entitlements_user ON entitlements (user_id);
