#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
npm install --no-package-lock
npm test
python -m pytest tests -q
