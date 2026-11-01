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
