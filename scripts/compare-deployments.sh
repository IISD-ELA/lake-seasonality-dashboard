#!/bin/bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STREAMLIT_URL="${STREAMLIT_URL:-http://127.0.0.1:8501}"

if [ -z "${AWS_URL:-}" ]; then
  AWS_URL="$(tofu -chdir="$ROOT_DIR/infrastructure/seasonality" output -raw site_url)"
fi

mkdir -p "$ROOT_DIR/build"
"$ROOT_DIR/scripts/start-streamlit-reference.sh" \
  > "$ROOT_DIR/build/streamlit-reference.log" 2>&1 &
STREAMLIT_PID=$!

cleanup ()
{
  kill "$STREAMLIT_PID" 2>/dev/null || true
  wait "$STREAMLIT_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 120)
do
  if curl -fsS "$STREAMLIT_URL/_stcore/health" > /dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "$STREAMLIT_URL/_stcore/health" > /dev/null

STREAMLIT_STATUS=0
AWS_STATUS=0
"$ROOT_DIR/scripts/test-browser.sh" "$STREAMLIT_URL" streamlit \
  || STREAMLIT_STATUS=$?
"$ROOT_DIR/scripts/test-browser.sh" "$AWS_URL" aws \
  || AWS_STATUS=$?

echo "Parity scenario results:"
echo "  Streamlit reference: $STREAMLIT_URL (exit $STREAMLIT_STATUS)"
echo "  AWS deployment:      $AWS_URL (exit $AWS_STATUS)"

if [ "$AWS_STATUS" -ne 0 ]; then
  exit 1
fi
