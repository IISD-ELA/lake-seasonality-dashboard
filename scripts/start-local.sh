#!/bin/bash
set -eo pipefail

usage ()
{
  echo 'Runs the AWS seasonality dashboard locally.'
  echo ''
  echo 'Usage: start-local.sh -r <region> -p <profile> -P <port>'
  echo ''
  echo '-region  | -r <aws-region>  Defaults to [ca-central-1]'
  echo '-profile | -p <aws-profile> Defaults to [iisd]'
  echo '-port    | -P <port>        Defaults to [8080]'
  exit 1
}

REGION='ca-central-1'
PROFILE='iisd'
PORT='8080'
ELA_API_ARN_PARAMETER='/iisd-ela/config/ela-api/arn'

while [ "$1" != "" ]
do
  case $1 in
    -region|-r ) shift
                  REGION=$1
                  ;;
    -profile|-p ) shift
                   PROFILE=$1
                   ;;
    -port|-P ) shift
                PORT=$1
                ;;
    -help|-h ) usage
               ;;
  esac
  shift
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="public.ecr.aws/lambda/python:3.14"

ELA_API_ARN="$(aws --profile "$PROFILE" --region "$REGION" ssm get-parameter \
  --name "$ELA_API_ARN_PARAMETER" \
  --query 'Parameter.Value' \
  --output text)"
ELA_API_ID="${ELA_API_ARN##*/}"

if [[ ! "$ELA_API_ID" =~ ^[a-z0-9]+$ ]]; then
  echo "Unable to derive the ELA API ID from $ELA_API_ARN_PARAMETER." >&2
  exit 1
fi

"$ROOT_DIR/scripts/package-lambda.sh"

docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  -p "$PORT:8080" \
  -e ELA_API_BASE_URL="https://${ELA_API_ID}.execute-api.${REGION}.amazonaws.com/dev" \
  -e ELA_API_MAX_ATTEMPTS='2' \
  -e ELA_API_TIMEOUT_SECONDS='8' \
  -e STATIC_DIR='/var/task/build/site' \
  -v "$ROOT_DIR:/var/task:ro" \
  -v "$ROOT_DIR/build/package:/opt/seasonality:ro" \
  "$IMAGE" \
  -lc 'PYTHONPATH=/opt/seasonality python -m seasonality_app.local_server --host 0.0.0.0 --port 8080'
