#!/usr/bin/env bash
# Run kanku's eval suite. Arguments go to `claude plugin eval`, e.g.:
#   evals/run.sh --scaffold --allow-tools Bash Write Edit
#   evals/run.sh --scaffold --case 'init-*' --runs 1
#
# The suite runs on a copy of the working tree (uncommitted changes
# included, ignored files left out), so what is measured is what is about to
# be committed, and results land in evals/results/ (ignored by git).
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
for tool in claude git tar; do
  command -v "$tool" >/dev/null 2>&1 || { echo "evals/run.sh: $tool is required" >&2; exit 2; }
done

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
(cd "$root" && git ls-files -z --cached --others --exclude-standard | tar --null -T - -cf -) | tar -xf - -C "$work"

# The default judge (haiku) misreads multi-part criteria, so the llm graders
# get a stronger judge unless the caller picks one.
judge=(--judge-model sonnet)
for argument in "$@"; do
  [[ "$argument" == --judge-model* ]] && judge=()
done

results="$root/evals/results/$(date -u +%Y-%m-%dT%H-%M-%SZ)"
mkdir -p "$results"
status=0
claude plugin eval "$work" --output-dir "$results" --report "$results/report.html" "${judge[@]}" "$@" || status=$?
echo "evals/run.sh: results in $results" >&2
exit "$status"
