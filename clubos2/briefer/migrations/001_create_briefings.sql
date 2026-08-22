CREATE TABLE IF NOT EXISTS briefings (
    briefing_id VARCHAR(64) PRIMARY KEY,
    briefing_type VARCHAR(50) NOT NULL,
    scope_key VARCHAR(200) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    triggered_by VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'generating',
    executive_summary TEXT,
    body_markdown TEXT,
    citations TEXT NOT NULL DEFAULT '[]',
    investigations_referenced TEXT NOT NULL DEFAULT '[]',
    alerts_referenced TEXT NOT NULL DEFAULT '[]',
    metrics_covered TEXT NOT NULL DEFAULT '[]',
    total_tokens INTEGER,
    cost_usd FLOAT,
    latency_seconds FLOAT,
    trace_url VARCHAR(500),
    freshness_days INTEGER NOT NULL DEFAULT 7,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_brf_scope_key ON briefings (scope_key);
CREATE INDEX IF NOT EXISTS idx_brf_briefing_type ON briefings (briefing_type);
CREATE INDEX IF NOT EXISTS idx_brf_period_end ON briefings (period_end DESC);
CREATE INDEX IF NOT EXISTS idx_brf_status ON briefings (status);
CREATE INDEX IF NOT EXISTS idx_brf_scope_completed ON briefings (scope_key, status, completed_at DESC)
