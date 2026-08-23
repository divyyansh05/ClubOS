ALTER TABLE metric_registry ADD COLUMN IF NOT EXISTS preferred_source VARCHAR(100);
ALTER TABLE metric_registry ADD COLUMN IF NOT EXISTS source_authority_note TEXT;
