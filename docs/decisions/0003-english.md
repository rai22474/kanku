# 0003 — kanku is written in English; the project's documents, in its language

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
The plugin — skills, process, formats — is in English. The documents a run
writes in a project are in the adapter's `language`, with heading sets
kanku ships per language.

## Why
A public plugin is read by people who share English; a project's documents
are read by its team, in theirs. The validator matches the shipped heading
set, so a project doesn't keep a second set of documents to satisfy it.
