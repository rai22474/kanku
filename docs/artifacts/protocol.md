# Protocol log

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

The project's own record of how benchmarks behave in *its* environment: the
conditions to check before launching, and every fix a run found. kanku's
process holds the general rules; this log holds the incidents that taught
them, here. At `docs.protocol`.

```markdown
# Benchmark protocol log

## Environment conditions

- The host firewall must accept the container bridge network, or the
  scenario stubs are unreachable and every scenario fails as environment.
- `notify_admin` reads `ADMIN_BOT_TOKEN`; it is in `side_effect_keys`.

## Resolved

### 2026-11-01 — Reasoning leaked into structured replies

**Found:** JSON parse errors only with candidates whose reasoning is
mandatory. **Root cause:** the reply builder concatenated every content
part, reasoning included. **Changed:** it keeps only the final text part
(commit a1b2c3d). Rows before the fix moved to history.
```

- **Environment conditions** is read before every launch (step 10).
- **Resolved** gets an entry the moment a fix is applied (step 12), never
  at the end of the run. Entries are appended; a resolved entry is never
  rewritten.
