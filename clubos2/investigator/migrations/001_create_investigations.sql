CREATE TABLE IF NOT EXISTS investigations (
    investigation_id VARCHAR(64) PRIMARY KEY,
    alert_id VARCHAR(64) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    triggered_by VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    cause_hypothesis TEXT,
    confidence VARCHAR(10),
    evidence_summary TEXT,
    citations TEXT NOT NULL DEFAULT '[]',
    reasoning_trace TEXT,
    tools_called TEXT,
    total_steps INTEGER,
    total_tokens INTEGER,
    cost_usd FLOAT,
    latency_seconds FLOAT,
    trace_url VARCHAR(500),
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inv_alert_id ON investigations (alert_id);
CREATE INDEX IF NOT EXISTS idx_inv_metric_name ON investigations (metric_name);
CREATE INDEX IF NOT EXISTS idx_inv_status ON investigations (status);
CREATE INDEX IF NOT EXISTS idx_inv_started_at ON investigations (started_at DESC)
