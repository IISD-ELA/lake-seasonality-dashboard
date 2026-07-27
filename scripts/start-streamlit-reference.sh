#!/bin/bash
set -eo pipefail

REGION="${AWS_REGION:-ca-central-1}"
PROFILE="${AWS_PROFILE:-iisd}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

STREAMLIT_WAF_SECRET="$(aws --profile "$PROFILE" --region "$REGION" ssm get-parameter \
  --name '/iisd-ela/config/config/waf/streamlit-secret' \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)"

export STREAMLIT_WAF_SECRET
exec "$ROOT_DIR/.venv/bin/streamlit" run "$ROOT_DIR/dashboard.py" \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --browser.gatherUsageStats false
