import pandas as pd

from seasonality_app.transforms import (
    set_baseline_ice,
    transform_cover,
    transform_dates,
)


def test_transform_dates_adds_original_dashboard_plot_columns():
    result = transform_dates(
        pd.DataFrame({"date": ["2025-02-15", "invalid"]}),
    )

    assert len(result) == 1
    assert result.iloc[0]["md"] == "02-15"
    assert result.iloc[0]["yr"] == "2025"
    assert result.iloc[0]["season_label"] == "2024/25"
    assert result.iloc[0]["season_x"] == pd.Timestamp("2001-02-15")


def test_transform_dates_handles_missing_or_invalid_data():
    assert transform_dates(pd.DataFrame()).empty
    assert transform_dates(pd.DataFrame({"other": [1]})).empty
    assert transform_dates(pd.DataFrame({"date": ["invalid"]})).empty


def test_transform_cover_and_baseline_are_guarded():
    cover = transform_cover(
        pd.DataFrame(
            {
                "start_date": ["2023-11-01", "2024-11-10"],
                "end_date": ["2024-05-01", "2025-05-01"],
            }
        )
    )
    result = set_baseline_ice(cover, col="days")

    assert list(result["yr"]) == [2023, 2024]
    assert "days_from_baseline" in result
    assert set_baseline_ice(pd.DataFrame(), col="days").empty
    assert transform_cover(pd.DataFrame({"start_date": []})).empty
