#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

APT_UPDATED=0

install_pkg() {
  if command -v apt-get >/dev/null 2>&1; then
    if [ "$APT_UPDATED" -eq 0 ]; then
      sudo apt-get update
      APT_UPDATED=1
    fi
    sudo apt-get install -y "$@"
    return
  fi

  echo "No supported package manager found. Install: $*" >&2
  exit 1
}

ensure_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    install_pkg python3 python3-venv
  fi
}

ensure_cmd() {
  local cmd="$1"
  shift
  if ! command -v "$cmd" >/dev/null 2>&1; then
    install_pkg "$@"
  fi
}

ensure_python_venv() {
  if python3 - <<'PY' >/dev/null 2>&1
import ensurepip
import venv
PY
  then
    return
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    echo "apt-get is required to install python3-venv." >&2
    exit 1
  fi

  py_ver="$(python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
  pkgs=(python3-venv)
  if command -v apt-cache >/dev/null 2>&1; then
    if apt-cache show "python${py_ver}-venv" >/dev/null 2>&1; then
      pkgs+=("python${py_ver}-venv")
    fi
  fi
  install_pkg "${pkgs[@]}"
}

ensure_python
ensure_cmd git git
ensure_cmd make make
ensure_python_venv

VENV="$ROOT/.venv"
VENV_PIP="$VENV/bin/pip"
if [ -d "$VENV" ] && [ ! -x "$VENV_PIP" ]; then
  sudo rm -rf "$VENV"
fi
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install wordfreq

SOURCES_DIR="$ROOT/sources"
SCOWL_DIR="$SOURCES_DIR/scowl"
mkdir -p "$SOURCES_DIR"

if [ ! -d "$SCOWL_DIR" ]; then
  git clone https://github.com/en-wl/wordlist "$SCOWL_DIR"
fi

sudo chown -R "$USER":"$USER" "$SCOWL_DIR"

if [ ! -x "$SCOWL_DIR/scowl" ]; then
  (cd "$SCOWL_DIR" && make)
fi

echo "Prep complete."
echo "Next: ./.venv/bin/python make_wordlist.py --wordfreq-list best --scowl-size 50 --max-len 15 --out english_le15.txt"
