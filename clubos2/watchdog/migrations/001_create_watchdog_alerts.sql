CREATE TABLE IF NOT EXISTS watchdog_alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    current_rank INTEGER NOT NULL,
    previous_rank INTEGER,
    rank_delta INTEGER,
    score_current FLOAT NOT NULL,
    score_previous FLOAT,
    triggered_by_rule VARCHAR(100) NOT NULL,
    context_snapshot TEXT NOT NULL,
    source VARCHAR(200) NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_watchdog_metric_name ON watchdog_alerts (metric_name);
CREATE INDEX IF NOT EXISTS idx_watchdog_run_id ON watchdog_alerts (run_id);
CREATE INDEX IF NOT EXISTS idx_watchdog_created_at ON watchdog_alerts (created_at)
