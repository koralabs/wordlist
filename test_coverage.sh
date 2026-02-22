#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv_coverage"
REPORT_FILE="$ROOT_DIR/test_coverage.report"
TMP_OUTPUT="$(mktemp)"
TMP_JSON="$(mktemp)"
trap 'rm -f "$TMP_OUTPUT" "$TMP_JSON"' EXIT

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip coverage

cd "$ROOT_DIR"
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage erase > /dev/null
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage run --branch --source=coverage_guardrail -m unittest tests.test_coverage_guardrail > "$TMP_OUTPUT" 2>&1
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage report -m --include='coverage_guardrail.py' >> "$TMP_OUTPUT" 2>&1
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage json -o "$TMP_JSON" --include='coverage_guardrail.py' > /dev/null 2>&1

cat "$TMP_OUTPUT" > "$REPORT_FILE"

read -r BRANCH_COVERAGE LINE_COVERAGE < <(
  python3 - "$TMP_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as handle:
    data = json.load(handle)

totals = data.get('totals', {})
num_statements = totals.get('num_statements', 0)
covered_lines = totals.get('covered_lines', 0)
num_branches = totals.get('num_branches', 0)
covered_branches = totals.get('covered_branches', 0)

line_pct = (covered_lines / num_statements * 100) if num_statements else 100.0
branch_pct = (covered_branches / num_branches * 100) if num_branches else 100.0

print(f"{branch_pct:.2f} {line_pct:.2f}")
PY
)

awk -v line="$LINE_COVERAGE" -v branch="$BRANCH_COVERAGE" 'BEGIN {
  if (line + 0 < 90 || branch + 0 < 90) exit 1;
}' || {
  echo "Coverage threshold not met (line=${LINE_COVERAGE}%, branch=${BRANCH_COVERAGE}%)." | tee -a "$REPORT_FILE"
  exit 1
}

echo "Coverage threshold met (line=${LINE_COVERAGE}%, branch=${BRANCH_COVERAGE}%)." | tee -a "$REPORT_FILE"
