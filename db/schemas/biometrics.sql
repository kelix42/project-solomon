-- biometrics.sql — Whoop signals; modulates the owner-state gate (Stage 9).

CREATE TABLE IF NOT EXISTS biometrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at     TEXT NOT NULL,
    recovery_pct    REAL,
    sleep_hours     REAL,
    strain          REAL,
    stress_flag     INTEGER NOT NULL DEFAULT 0,   -- 0 = no, 1 = yes
    raw_payload     TEXT                          -- full JSON from Whoop API
);
CREATE INDEX IF NOT EXISTS idx_biometrics_captured ON biometrics(captured_at);
