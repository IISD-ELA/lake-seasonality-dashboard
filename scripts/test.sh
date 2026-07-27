#!/bin/bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="public.ecr.aws/lambda/python:3.14"

"$ROOT_DIR/scripts/package-lambda.sh"

docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  -e HOME=/tmp \
  -e PYTHONPATH=/opt/seasonality:/src \
  -v "$ROOT_DIR:/src:ro" \
  -v "$ROOT_DIR/build/package:/opt/seasonality:ro" \
  "$IMAGE" \
  -lc 'python -m pip install --quiet --target /tmp/test-deps pytest==8.4.2
PYTHONPATH=/tmp/test-deps:$PYTHONPATH python -m pytest \
  -o cache_dir=/tmp/pytest-cache \
  -m "not browser" \
  /src/tests'
