# ELA Seasonality Dashboard

Author: Delvin So
AWS port: IISD Data and Technology team

This repository contains the IISD Experimental Lakes Area seasonality
dashboard. The production architecture is a static browser application backed
by an AWS Lambda API. The original Streamlit implementation remains unchanged
in `dashboard.py`, `get_data.py`, `plot.py`, and `iisd_colours.py` so it can be
run as a parity reference during the migration.

Data is fetched from [ELA's Data API](https://github.com/IISD-ELA/ela-api).

## AWS Architecture

```text
Browser
  |
  v
CloudFront
  |-- static requests --> private S3 bucket
  |
  `-- /api/* ----------> HTTP API Gateway --> Python 3.14 Lambda
                                                   |
                                                   v
                                           ELA Data API + WAF
```

- **CloudFront** provides one HTTPS origin for the browser, caches static files,
  and caches successful data responses. Only `comparison_year` is included in
  the API cache key; degraded responses are returned with `no-store`.
- **S3** stores the HTML, CSS, JavaScript, fonts, logo, and the matching
  `plotly.js` browser bundle. The bucket is private and accessible only through
  CloudFront Origin Access Control.
- **API Gateway HTTP API** exposes the Lambda routes with a 29-second
  integration timeout.
- **Lambda** fetches independent ELA API datasets concurrently, applies the
  existing pandas transformations, and uses the unchanged `plot.py` functions
  to return Plotly figure JSON.
- **CloudWatch Logs and alarms** record upstream failures while the browser
  receives a fixed, non-sensitive unavailable message. Alarms cover repeated
  upstream failures, unhandled Lambda errors, and HTTP API 5xx responses.
- **S3 deployment artifacts** hold the zipped Lambda package. This avoids the
  direct Lambda upload limit while retaining the preferred zip deployment
  model. Packaging fails if the uncompressed artifact exceeds 220 MB.
- **OpenTofu state** is stored in the existing `terraform-state-iisd-ela`
  backend under `lake-seasonality-dashboard/terraform.tfstate`.

The ELA API identifier is not hardcoded. OpenTofu reads
`/iisd-ela/config/ela-api/arn` from SSM Parameter Store and derives the API base
URL. `scripts/start-local.sh` performs the same lookup with the AWS CLI.

### WAF Behavior

The ELA API WAF blocks generic machine user agents but permits browser traffic.
The AWS Lambda therefore retains the browser-style user agent used by the
original application. It does **not** retrieve or send `x-streamlit-secret`.

The existing Streamlit deployment still requires that secret, so the shared WAF
exception and SSM parameter must remain until Streamlit is retired. The helper
`scripts/start-streamlit-reference.sh` reads the secret only for running the
unchanged reference application.

## API Routes

| Route | Purpose | CloudFront shared cache |
| --- | --- | --- |
| `GET /api/ice-history` | Ice off, ice on, and ice cover history | Up to 1 hour |
| `GET /api/ice-off?comparison_year=YYYY` | Snow, air temperature, and ice-off comparison | Up to 15 minutes |
| `GET /api/lake-turnover` | Thermocline and lake surface temperature | Up to 15 minutes |
| `GET /health` | Lambda health check | Disabled |

`comparison_year` is accepted only as an integer from 2000 through the year
before the current year. No arbitrary query parameters are forwarded to the ELA
API.

CloudFront adds a Content Security Policy. Framing is limited to the dashboard
itself and `https://www.iisd.org` for the IISD website embed. Set the OpenTofu
`frame_ancestors` variable to change the trusted CSP sources. Set
`alarm_sns_topic_arn` to an existing SNS topic ARN to send upstream-failure and
recovery notifications. CSP permits inline styles because Plotly injects them
while rendering and resizing charts.

Lambda remains at 1024 MB. Testing at 1769 MB reduced measured cold-start time
by only about 6% while increasing configured memory by 73%, so the higher
setting was not retained.

## Repository Layout

```text
.
|-- dashboard.py                    # unchanged Streamlit reference
|-- get_data.py                     # unchanged Streamlit data client
|-- plot.py                         # shared Plotly figure builders
|-- iisd_colours.py                 # shared IISD palette
|-- src/seasonality_app/            # Lambda API and local server
|-- web/                            # AWS browser application
|-- static/                         # original fonts, logos, and Streamlit CSS
|-- infrastructure/seasonality/     # OpenTofu AWS infrastructure
|-- scripts/                        # package, run, test, and deploy helpers
`-- tests/                          # unit, figure parity, and browser tests
```

## Prerequisites

- AWS CLI authenticated with the `iisd` profile
- Docker
- OpenTofu
- Python 3 for browser test tooling

AWS Lambda Python 3.14 and `public.ecr.aws/lambda/python:3.14` are used
consistently for packaging, local execution, and deployment.

## Package and Test

Build the Lambda zip and static site:

```bash
scripts/package-lambda.sh
```

The generated artifacts are:

```text
build/lambda.zip
build/package/
build/site/
```

Run unit and Plotly figure-parity tests in the Python 3.14 Lambda image:

```bash
scripts/test.sh
```

## Run Locally

Run the AWS application locally on port 8080:

```bash
scripts/start-local.sh -p iisd -r ca-central-1 -P 8080
```

Open `http://127.0.0.1:8080`. The script reads the ELA API ARN from SSM,
packages the application, and starts a Lambda-compatible Python 3.14 container.

To run the unchanged Streamlit reference:

```bash
scripts/start-streamlit-reference.sh
```

Open `http://127.0.0.1:8501`.

## Deploy

Deploy the package, infrastructure, and static site:

```bash
scripts/deploy.sh -p iisd -r ca-central-1
```

The script:

1. Builds the Python 3.14 Lambda zip and static site.
2. Initializes OpenTofu with the shared remote backend.
3. Applies the `infrastructure/seasonality` stack.
4. Invalidates CloudFront so updated frontend assets are visible. The HTML,
   application JavaScript, and CSS also use `no-cache` to prevent mixed
   frontend versions.
5. Prints the CloudFront URL, API endpoint, and Lambda function name.

No source code is pushed by the deployment script.

## Browser Parity Tests

Run the common workflow suite against any one deployment:

```bash
scripts/test-browser.sh http://127.0.0.1:8501 streamlit
scripts/test-browser.sh https://example.cloudfront.net aws
```

After deployment, run the complete comparison. It starts the unchanged local
Streamlit app, obtains the AWS URL from OpenTofu output, and runs the same
spring-tab, year-confirmation, fall-tab, and non-empty-chart scenarios against
both:

```bash
scripts/compare-deployments.sh
```

The helper runs both suites even if one fails and prints each exit status. The
unchanged Streamlit result is informational because its upstream LST failure is
outside this migration; the helper returns nonzero only when the AWS suite
fails. Screenshots are written to `build/test-artifacts/`.
