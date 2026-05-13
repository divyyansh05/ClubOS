# ClubOS Refresh Runbook

## Purpose

Define the recurring monthly refresh workflow for ClubOS.

## Monthly Refresh Flow

1. Receive updated internal workbook
2. Receive updated benchmark workbook
3. Validate file names, sheets, and expected columns
4. Ingest raw files into Bronze
5. Run Silver normalization and quality checks
6. Rebuild Gold tables
7. Validate:
   - KPI health
   - benchmark outputs
   - signal outputs
   - priority outputs
8. Refresh backend-facing and frontend-facing outputs
9. Generate Monthly Briefing

## Failure Handling

If validation fails:

- stop the refresh
- log the failing check
- preserve previous successful Gold outputs
- report the error clearly

## Product Principle

Each refresh should preserve the same app behavior:

- same screens
- same logic
- same workflow
- new month of business answers
