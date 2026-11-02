# Changelog

[README](README.md)

All notable changes to kanku. Versions follow [semantic versioning](https://semver.org);
a change to the adapter format is a major version.

## Unreleased

- The process (`docs/process/`), the document formats (`docs/artifacts/`),
  the measurement contract, the adapter draft and kanku's own decision
  records, extracted from the model-selection process of the project it
  grew in.
- `scripts/kanku`: the launch gates (trust, pinned variables, side-effect
  keys, nothing running — no value ever printed), the benchmark runner (env
  swap restored on exit, fresh compose stack per repetition, the dataset's
  scenarios) and the report (exact per-call latency, effective cost with
  cache, failure classes, the 16-column row, a per-scenario breakdown).
  Its tests include a real run whose recorded row the report reproduces.
- `scripts/kanku check` and the `PostToolUse` hook: the validator of
  `docs/artifacts/` — every adapter variable covered, candidate status
  consistent with its table and decision, no pending word in a decided
  section, result rows of one section measured on the same code, results,
  history and revision entries only appended (against `HEAD`, or
  `--base` in CI), scenarios fixed once measured, a record per decided
  variable. The hook blocks an edit of one of these documents with that
  file's problems.
- Skills: `init` (writes the adapter from what the project has, never
  reading the env file), `trust` (user-only), `run` (drives the process
  from `docs/process/`, stops without adapter or catalog, launches no
  benchmark on an unapproved adapter). Evals for each rule in `evals/`.
