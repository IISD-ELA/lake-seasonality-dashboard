import json

from seasonality_app import handler


def invoke(path, query=None):
    return handler.handler(
        {"rawPath": path, "queryStringParameters": query or {}},
        None,
    )


def test_health():
    response = invoke("/health")

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "ok"}
    assert response["headers"]["Cache-Control"] == "no-store"


def test_ice_off_validates_query(monkeypatch):
    monkeypatch.setattr(
        handler,
        "build_ice_off",
        lambda value: (_ for _ in ()).throw(ValueError("invalid year")),
    )

    response = invoke("/api/ice-off", {"comparison_year": "nope"})

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "invalid year"}


def test_routes_return_cacheable_payloads(monkeypatch):
    monkeypatch.setattr(
        handler,
        "build_ice_history",
        lambda: {"figure": {}, "errors": {}},
    )
    monkeypatch.setattr(
        handler,
        "build_ice_off",
        lambda year: {
            "comparison_year": int(year),
            "figure": {},
            "errors": {},
        },
    )
    monkeypatch.setattr(
        handler,
        "build_lake_turnover",
        lambda: {
            "thermocline_figure": {},
            "lake_temperature_figure": {},
            "errors": {},
        },
    )

    history = invoke("/api/ice-history")
    ice_off = invoke("/api/ice-off", {"comparison_year": "2024"})
    turnover = invoke("/api/lake-turnover")

    assert history["statusCode"] == 200
    assert "s-maxage=3600" in history["headers"]["Cache-Control"]
    assert json.loads(ice_off["body"])["comparison_year"] == 2024
    assert "s-maxage=900" in turnover["headers"]["Cache-Control"]


def test_degraded_payloads_are_not_cached(monkeypatch):
    monkeypatch.setattr(
        handler,
        "build_lake_turnover",
        lambda: {
            "thermocline_figure": {},
            "lake_temperature_figure": None,
            "errors": {
                "lake_surface_temperature": (
                    "Lake surface temperature data is unavailable."
                )
            },
        },
    )

    response = invoke("/api/lake-turnover")

    assert response["statusCode"] == 200
    assert response["headers"]["Cache-Control"] == "no-store"


def test_unknown_route():
    response = invoke("/missing")

    assert response["statusCode"] == 404
