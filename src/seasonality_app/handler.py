"""AWS Lambda entry point."""

import json
import logging

from plotly.utils import PlotlyJSONEncoder

from .service import build_ice_history, build_ice_off, build_lake_turnover


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def _response(status_code, body, cache_control="no-store"):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": cache_control,
        },
        "body": json.dumps(body, cls=PlotlyJSONEncoder, separators=(",", ":")),
    }


def _data_response(body, cache_control):
    if body.get("errors"):
        cache_control = "no-store"
    return _response(200, body, cache_control)


def handler(event, _context):
    path = event.get("rawPath") or event.get("path") or "/"
    query = event.get("queryStringParameters") or {}

    try:
        if path == "/health":
            return _response(200, {"status": "ok"})
        if path == "/api/ice-history":
            return _data_response(
                build_ice_history(),
                "public, max-age=300, s-maxage=3600",
            )
        if path == "/api/ice-off":
            return _data_response(
                build_ice_off(query.get("comparison_year")),
                "public, max-age=120, s-maxage=900",
            )
        if path == "/api/lake-turnover":
            return _data_response(
                build_lake_turnover(),
                "public, max-age=120, s-maxage=900",
            )
        return _response(404, {"error": "Not found"})
    except ValueError as exc:
        return _response(400, {"error": str(exc)})
    except Exception:
        LOGGER.exception("Unhandled request failure for %s", path)
        return _response(502, {"error": "Dashboard data is temporarily unavailable."})
