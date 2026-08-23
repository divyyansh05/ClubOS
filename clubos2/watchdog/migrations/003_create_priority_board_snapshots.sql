CREATE TABLE IF NOT EXISTS priority_board_snapshots (
    snapshot_id VARCHAR(64) PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL,
    source_path TEXT NOT NULL,
    rows_json TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pbs_captured_at ON priority_board_snapshots (captured_at);
