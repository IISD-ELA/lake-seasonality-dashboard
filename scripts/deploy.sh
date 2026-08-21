#!/bin/bash
set -eo pipefail

usage ()
{
  echo 'Deploys the IISD-ELA seasonality dashboard to AWS.'
  echo ''
  echo 'Usage: deploy.sh -r <region> -p <profile>'
  echo ''
  echo '-region  | -r <aws-region>  Defaults to [ca-central-1]'
  echo '-profile | -p <aws-profile> Defaults to [iisd]'
  exit 1
}

REGION='ca-central-1'
PROFILE='iisd'

while [ "$1" != "" ]
do
  case $1 in
    -region|-r ) shift
                  REGION=$1
                  ;;
    -profile|-p ) shift
                   PROFILE=$1
                   ;;
    -help|-h ) usage
               ;;
  esac
  shift
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

pushd "$ROOT_DIR" > /dev/null

scripts/package-lambda.sh

pushd infrastructure/seasonality > /dev/null

tofu init -reconfigure \
  -backend-config="region=$REGION" \
  -backend-config="profile=$PROFILE"

tofu apply -auto-approve \
  -var="aws_region=$REGION" \
  -var="aws_profile=$PROFILE"

DISTRIBUTION_ID="$(tofu output -raw cloudfront_distribution_id)"
SITE_URL="$(tofu output -raw site_url)"
API_ENDPOINT="$(tofu output -raw api_endpoint)"
LAMBDA_FUNCTION_NAME="$(tofu output -raw lambda_function_name)"

popd > /dev/null

aws --profile "$PROFILE" --region "$REGION" cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" > /dev/null

echo "Site URL: $SITE_URL"
echo "API endpoint: $API_ENDPOINT"
echo "Lambda function: $LAMBDA_FUNCTION_NAME"

popd > /dev/null
