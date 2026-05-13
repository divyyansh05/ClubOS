# Event Annotations Contract

## Purpose

Define the format for manually curated event annotations used by the Event Intelligence layer.

## Recommended Storage

- `databricks/seeds/event_annotations.csv`

## Required Columns

- `event_id`
- `event_name`
- `event_type`
- `event_month`
- `event_scope`
- `description`

## Field Guidance

### `event_id`

- stable unique identifier

### `event_name`

- human-readable title

### `event_type`

Suggested values:

- `shared_shock`
- `trophy`
- `major_signing`
- `major_exit`
- `business_milestone`

### `event_month`

- month-start date

### `event_scope`

Suggested values:

- `real_madrid`
- `multi_club`

## MVP Guidance

The MVP should include:

- COVID
- 2 to 4 major football/business events with clean month anchors
