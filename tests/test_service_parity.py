import json

import pandas as pd
from plotly.utils import PlotlyJSONEncoder

from plot import stack_snow_and_air
from seasonality_app import service
from seasonality_app.transforms import transform_dates


def canonical(value):
    return json.dumps(value, cls=PlotlyJSONEncoder, sort_keys=True)


def test_ice_off_figure_matches_original_plotting_path(monkeypatch):
    current_year = pd.Timestamp.now().year
    comparison_year = current_year - 1
    fixtures = {
        "ice_extremes": pd.DataFrame(
            {
                "activity_start_date": ["1998-04-20", "2014-05-16"],
                "type": ["min", "max"],
            }
        ),
        "ice_off_dates": pd.DataFrame(
            {
                "date": [
                    f"{comparison_year}-05-01",
                    f"{current_year}-05-04",
                ]
            }
        ),
        "snow_depth": pd.DataFrame(
            {
                "date": [
                    f"{comparison_year}-02-15",
                    f"{comparison_year}-03-15",
                    f"{current_year}-02-15",
                    f"{current_year}-03-15",
                ],
                "snow_depth": [50.0, 32.0, 45.0, 28.0],
            }
        ),
        "air_temperature": pd.DataFrame(
            {
                "date": [
                    f"{comparison_year}-02-15",
                    f"{comparison_year}-03-15",
                    f"{current_year}-02-15",
                    f"{current_year}-03-15",
                ],
                "avg_temp": [-15.0, -3.0, -12.0, -1.0],
            }
        ),
    }
    monkeypatch.setattr(
        service,
        "fetch_parallel",
        lambda _callables: (fixtures, {}),
    )

    actual = service.build_ice_off(comparison_year)["figure"]

    expected = stack_snow_and_air(
        transform_dates(fixtures["snow_depth"]),
        transform_dates(fixtures["air_temperature"]),
        transform_dates(fixtures["ice_extremes"], "activity_start_date"),
        transform_dates(fixtures["ice_off_dates"]),
    ).to_plotly_json()
    assert canonical(actual) == canonical(expected)


def test_comparison_year_is_strictly_whitelisted():
    current_year = pd.Timestamp.now().year

    assert service.validate_comparison_year("2000", current_year) == 2000
    assert (
        service.validate_comparison_year(str(current_year - 1), current_year)
        == current_year - 1
    )

    for value in ("1999", str(current_year), "2024,2025", "../2024", None):
        try:
            service.validate_comparison_year(value, current_year)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected {value!r} to be rejected")
