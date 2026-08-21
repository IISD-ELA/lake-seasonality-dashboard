#!/bin/bash
set -eo pipefail

usage ()
{
  echo 'Runs browser parity tests against one dashboard URL.'
  echo ''
  echo 'Usage: test-browser.sh <base-url> <aws|streamlit>'
  exit 1
}

BASE_URL="${1:-}"
APP_VARIANT="${2:-}"
if [ -z "$BASE_URL" ] || [[ ! "$APP_VARIANT" =~ ^(aws|streamlit)$ ]]; then
  usage
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_VENV="$ROOT_DIR/.test-venv"

if [ ! -x "$TEST_VENV/bin/python" ]; then
  python3 -m venv "$TEST_VENV"
fi

"$TEST_VENV/bin/python" -m pip install --quiet -r "$ROOT_DIR/requirements-dev.txt"
"$TEST_VENV/bin/python" -m playwright install chromium > /dev/null

TMPDIR=/tmp TEMP=/tmp TMP=/tmp \
BASE_URL="${BASE_URL%/}" APP_VARIANT="$APP_VARIANT" \
  "$TEST_VENV/bin/python" -m pytest -m browser "$ROOT_DIR/tests/test_browser_parity.py"
