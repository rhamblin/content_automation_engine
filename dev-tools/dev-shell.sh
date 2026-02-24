#!/usr/bin/env bash
set -e

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

. .venv/bin/activate
pip install -q redis
pip install -q -e ./common
for req in dev-tools/*/requirements.txt; do pip install -q -r "$req"; done
