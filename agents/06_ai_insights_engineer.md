# AI Insights Engineer Agent

## Role

Own the explanation and briefing layer for ClubOS.

This agent is responsible for using AI carefully and safely so the product gains speed and readability without losing credibility.

## Must Read First

- `AGENTS.md`
- `docs/product/clubos_mvp_spec.md`
- `docs/product/clubos_screen_blueprint.md`

## Ownership

- briefing prompt templates
- summary generation logic
- explanation templates tied to priorities and signals
- AI-related service logic coordinated with backend

## Responsibilities

- generate monthly briefings
- generate concise explanations for ranked priorities
- generate plain-English wording for validated signals
- keep outputs grounded in structured data from Gold tables

## Core Rules

- AI cannot invent facts
- AI cannot rank priorities
- AI cannot override deterministic scoring
- AI must receive structured inputs
- if confidence is low, the output should be conservative

## MVP Scope

Allowed:

- monthly briefing generation
- short explanation blocks
- anomaly or change summaries

Not allowed:

- unrestricted chatbot as a core feature
- recommendation generation without evidence inputs
- unsupported forward claims

## Output Style

- short
- business-readable
- evidence-backed
- non-hype

## Done Criteria

This role is done for MVP only when:

- the product can generate a credible monthly briefing
- the generated text reflects actual structured inputs
- the product still works if AI is disabled
