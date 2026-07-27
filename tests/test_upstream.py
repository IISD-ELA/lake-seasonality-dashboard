from seasonality_app import upstream


class StubResponse:
    status_code = 200
    text = '{"data":[{"date":"2025-01-01","value":1}]}'

    def raise_for_status(self):
        return None


def test_upstream_uses_browser_user_agent_without_streamlit_secret(
    monkeypatch,
):
    captured = {}

    def fake_get(url, params, headers, timeout):
        captured.update(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return StubResponse()

    monkeypatch.setenv("ELA_API_BASE_URL", "https://example.test/dev")
    monkeypatch.setattr(upstream.requests, "get", fake_get)

    result = upstream.fetch_df("ice", {"kind": "extremes"})

    assert len(result) == 1
    assert captured["url"] == "https://example.test/dev/ice"
    assert captured["headers"]["User-Agent"].startswith("Mozilla/5.0")
    assert "x-streamlit-secret" not in {
        name.lower() for name in captured["headers"]
    }


def test_upstream_normalizes_nonstandard_nan_values(monkeypatch):
    response = StubResponse()
    response.text = '{"data":[{"date":"2025-01-01","value":NaN}]}'

    monkeypatch.setenv("ELA_API_BASE_URL", "https://example.test/dev")
    monkeypatch.setattr(
        upstream.requests,
        "get",
        lambda *_args, **_kwargs: response,
    )

    result = upstream.fetch_df("air_temp", {})

    assert result["value"].isna().all()


def test_api_base_is_required(monkeypatch):
    monkeypatch.delenv("ELA_API_BASE_URL", raising=False)

    try:
        upstream.fetch_df("ice", {"kind": "extremes"})
    except RuntimeError as exc:
        assert "ELA_API_BASE_URL" in str(exc)
    else:
        raise AssertionError("Expected missing API base configuration to fail")


def test_parallel_failures_are_logged_and_sanitized(caplog):
    sensitive_detail = "database relation internal.secret_table is missing"

    def fail():
        raise RuntimeError(sensitive_detail)

    with caplog.at_level("WARNING"):
        results, errors = upstream.fetch_parallel({"lake_temperature": fail})

    assert results == {}
    assert errors == {
        "lake_temperature": upstream.UPSTREAM_UNAVAILABLE_MESSAGE,
    }
    assert sensitive_detail not in errors["lake_temperature"]
    assert "UPSTREAM_FAILURE name=lake_temperature" in caplog.text
