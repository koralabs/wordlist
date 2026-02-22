#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv_coverage"
REPORT_FILE="$ROOT_DIR/test_coverage.report"
TMP_DIR="$(mktemp -d)"
TMP_JSON="$TMP_DIR/coverage.json"
trap 'rm -rf "$TMP_DIR"' EXIT

THRESHOLD_LINES=90
THRESHOLD_BRANCHES=90
SOURCE_PATHS="make_wordlist.py;compare_handles.py"
EXCLUDED_PATHS="prep.sh:bash-runtime-script-with-non-measurable-line-branch-coverage-in-current-toolchain; docs/**:documentation-content; tests/**:test-code; coverage_guardrail.py:removed-synthetic-artifact"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip coverage

cd "$ROOT_DIR"

PYTHONPATH=. "$VENV_DIR/bin/python" -m unittest discover -s tests -p 'test_*.py' > "$TMP_DIR/python.unittest.log" 2>&1

PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage erase > /dev/null
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage run --branch --source=make_wordlist,compare_handles -m unittest discover -s tests -p 'test_*.py' > "$TMP_DIR/python.coverage.run.log" 2>&1
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage report -m --include='make_wordlist.py,compare_handles.py' > "$TMP_DIR/python.coverage.report.log" 2>&1
PYTHONPATH=. "$VENV_DIR/bin/python" -m coverage json -o "$TMP_JSON" --include='make_wordlist.py,compare_handles.py' > /dev/null 2>&1

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

STATUS="partial"
PYTHON_STATUS="pass"
if awk -v line="$LINE_COVERAGE" -v branch="$BRANCH_COVERAGE" -v tl="$THRESHOLD_LINES" -v tb="$THRESHOLD_BRANCHES" 'BEGIN { exit !((line + 0 < tl) || (branch + 0 < tb)) }'; then
  STATUS="fail"
  PYTHON_STATUS="fail"
fi

{
  echo "FORMAT_VERSION=1"
  echo "REPO=wordlist"
  echo "TIMESTAMP_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "THRESHOLD_LINES=$THRESHOLD_LINES"
  echo "THRESHOLD_BRANCHES=$THRESHOLD_BRANCHES"
  echo "TOTAL_LINES_PCT=$LINE_COVERAGE"
  echo "TOTAL_BRANCHES_PCT=$BRANCH_COVERAGE"
  echo "STATUS=$STATUS"
  echo "SOURCE_PATHS=$SOURCE_PATHS"
  echo "EXCLUDED_PATHS=$EXCLUDED_PATHS"
  echo "LANGUAGE_SUMMARY=python:lines=$LINE_COVERAGE,branches=$BRANCH_COVERAGE,tool=coverage.py,status=$PYTHON_STATUS;bash:lines=NA,branches=NA,tool=unittest-script-check,status=na"
  echo
  echo "=== RAW_OUTPUT_PYTHON_UNITTEST ==="
  cat "$TMP_DIR/python.unittest.log"
  echo
  echo "=== RAW_OUTPUT_PYTHON_COVERAGE_RUN ==="
  cat "$TMP_DIR/python.coverage.run.log"
  echo
  echo "=== RAW_OUTPUT_PYTHON_COVERAGE_REPORT ==="
  cat "$TMP_DIR/python.coverage.report.log"
} > "$REPORT_FILE"

if [[ "$STATUS" == "fail" ]]; then
  echo "Coverage threshold not met (line=${LINE_COVERAGE}%, branch=${BRANCH_COVERAGE}%)." >&2
  exit 1
fi

echo "Coverage threshold met for measurable python scope (line=${LINE_COVERAGE}%, branch=${BRANCH_COVERAGE}%)."
