# Evals

[README](../README.md) · [Docs](../docs/index.md)

One case per critical skill rule, in the `claude plugin eval` format
(`<case>/prompt.md`, `case.yaml`, `graders/`). Each case seeds its project
with `fixture.sh`, which only runs with `--scaffold`.

```bash
evals/run.sh --scaffold --allow-tools Bash Write Edit             # every case, with a no-plugin baseline
evals/run.sh --scaffold --allow-tools Bash Write Edit --tag init  # one tag
```

**Requirements:** granting `Bash` needs Claude Code's sandbox — on Linux,
`bubblewrap` and `socat` installed. Without it every run is refused before
it starts.

The first run in a terminal asks whether you trust the plugin directory;
from a script or another Claude session, pass `--trust-plugin`.

**Reading the results:** each case also runs without the plugin. A case
that scores the same both ways (Δ = 0) guards a rule Claude already follows
from the fixture's context — a regression net, not evidence of what the
plugin adds. One run per case (`--runs 1`) finds clear failures; the
default of three shows whether a pass is stable.

A skill change starts here: add the case that fails today, change the
skill, and keep every case green.

| Case | Rule it guards |
|---|---|
| run-without-adapter-offers-init | No adapter → offer `/kanku:init`; don't guess a layout or write one. |
| run-without-catalog-stops | No OpenRouter catalog → stop and ask for it; never choose a model, quote prices or write candidates from memory. |
| init-never-reads-the-env-file | init maps the env file, the variables and the side-effect keys by name, without reading or printing the env file. |
| trust-is-the-users-call | Asked to approve the adapter, Claude leaves it to the user's `/kanku:trust`. |
