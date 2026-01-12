#!/usr/bin/env bash
set -e

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

. .venv/bin/activate
pip install -q redis
# pip install -q -e ./common
pip install --no-cache-dir -e ./common

