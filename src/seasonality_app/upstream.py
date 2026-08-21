"""ELA Data API client used by the AWS dashboard."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
import time
from json.decoder import JSONDecodeError

import pandas as pd
import requests


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
UPSTREAM_UNAVAILABLE_MESSAGE = "Requested data is temporarily unavailable."
LOGGER = logging.getLogger(__name__)


class UpstreamError(RuntimeError):
    """Raised when the ELA Data API cannot satisfy a request."""


def _api_base():
    value = os.getenv("ELA_API_BASE_URL", "").strip().rstrip("/")
    if not value:
        raise RuntimeError("ELA_API_BASE_URL is not configured")
    return value


def _request_data(endpoint, params):
    attempts = max(1, int(os.getenv("ELA_API_MAX_ATTEMPTS", "2")))
    timeout = float(os.getenv("ELA_API_TIMEOUT_SECONDS", "8"))
    url = f"{_api_base()}/{endpoint.lstrip('/')}"
    headers = {
        # The shared ELA API WAF accepts browser traffic and blocks generic
        # machine clients. The old Streamlit-only shared secret is not used.
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "application/json",
    }

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < attempts:
                time.sleep(0.5 * attempt)
                continue
            response.raise_for_status()
            # The ELA API currently emits bare NaN values for missing
            # measurements. Normalize those non-standard JSON constants to
            # null so Python 3.14 can parse the otherwise valid response.
            payload = json.loads(
                response.text,
                parse_constant=lambda _constant: None,
            )
            if isinstance(payload, dict) and "body" in payload:
                payload = payload["body"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            data = payload.get("data", []) if isinstance(payload, dict) else []
            if not isinstance(data, list):
                raise UpstreamError(f"{endpoint} returned an invalid data payload")
            return data
        except (requests.RequestException, JSONDecodeError, UpstreamError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(0.5 * attempt)

    raise UpstreamError(f"{endpoint} request failed: {last_error}") from last_error


def fetch_df(endpoint, params):
    return pd.DataFrame.from_records(_request_data(endpoint, params))


def get_lst_data(measurement_type="daily"):
    return fetch_df(
        "lst",
        {"months": "9,10,11", "agg": measurement_type.lower()},
    )


def get_ice_data(kind="off", years=()):
    params = {"kind": kind}
    if kind == "off" and years:
        params["years"] = ",".join(map(str, tuple(years)[:2]))
    return fetch_df("ice", params)


def get_snow_depth_data(years=()):
    return fetch_df(
        "snow_depth",
        {
            "months": "2,3,4,5",
            "years": ",".join(map(str, tuple(years)[:2])),
        },
    )


def get_air_temp_data(years=()):
    return fetch_df(
        "air_temp",
        {
            "months": "2,3,4,5",
            "years": ",".join(map(str, tuple(years)[:2])),
        },
    )


def get_thermocline_data():
    return fetch_df("thermocline", {"months": "9,10,11"})


def fetch_parallel(callables):
    """Run independent upstream requests concurrently and retain partial results."""
    results = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=len(callables)) as executor:
        futures = {
            executor.submit(callback): name for name, callback in callables.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception:  # Each panel reports its own unavailable state.
                LOGGER.warning(
                    "UPSTREAM_FAILURE name=%s",
                    name,
                    exc_info=True,
                )
                errors[name] = UPSTREAM_UNAVAILABLE_MESSAGE
    return results, errors
