# Data Folder

This folder contains raw source material and local source packs used to build ClubOS.

Recommended structure:

- `source/` for original provided files
- `processed/` for local non-authoritative exports if ever needed

Source-of-truth product outputs should not live here. They should be generated in Databricks and exposed through Gold tables.
