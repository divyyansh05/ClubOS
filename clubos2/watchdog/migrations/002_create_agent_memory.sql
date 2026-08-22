CREATE TABLE IF NOT EXISTS agent_memory (
    memory_id VARCHAR(64) PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    subject_key VARCHAR(200) NOT NULL,
    subject_metadata TEXT,
    occurred_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    confidence FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_subject ON agent_memory (agent_name, subject_key);
CREATE INDEX IF NOT EXISTS idx_agent_memory_occurred_at ON agent_memory (occurred_at)
