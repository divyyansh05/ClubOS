CREATE TABLE IF NOT EXISTS metric_registry (
    metric_name VARCHAR(100) PRIMARY KEY,
    business_name VARCHAR(200) NOT NULL,
    definition TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    polarity VARCHAR(10) NOT NULL CHECK (polarity IN ('positive', 'negative')),
    unit VARCHAR(50),
    ambiguous_with VARCHAR(500),
    disambiguation_rule TEXT,
    seasonal_note TEXT,
    typical_range VARCHAR(100),
    valid_query_examples TEXT,
    invalid_query_examples TEXT,
    skill_file_path VARCHAR(500),
    owned_by VARCHAR(100),
    last_reviewed TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
