"""Build Plotly figures for the dashboard API."""

from datetime import UTC, datetime

import pandas as pd

from plot import plot_lst, plot_thermocline, stack_ice_figs, stack_snow_and_air

from .transforms import (
    has_columns,
    set_baseline_ice,
    transform_cover,
    transform_dates,
)
from .upstream import (
    fetch_parallel,
    get_air_temp_data,
    get_ice_data,
    get_lst_data,
    get_snow_depth_data,
    get_thermocline_data,
)


MIN_COMPARISON_YEAR = 2000


def _timestamp():
    return datetime.now(UTC).isoformat()


def _figure_json(figure):
    return figure.to_plotly_json()


def validate_comparison_year(value, current_year=None):
    current_year = current_year or pd.Timestamp.now().year
    max_comparison_year = current_year - 1
    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("comparison_year must be a four-digit year") from exc
    if year < MIN_COMPARISON_YEAR or year > max_comparison_year:
        raise ValueError(
            "comparison_year must be between "
            f"{MIN_COMPARISON_YEAR} and {max_comparison_year}"
        )
    return year


def build_ice_history():
    data, errors = fetch_parallel(
        {
            "ice_off": lambda: get_ice_data(kind="off"),
            "ice_on": lambda: get_ice_data(kind="on"),
            "ice_cover": lambda: get_ice_data(kind="cover"),
        }
    )

    off = transform_dates(data.get("ice_off", pd.DataFrame()), "date")
    on = transform_dates(data.get("ice_on", pd.DataFrame()), "date")
    cover = transform_cover(data.get("ice_cover", pd.DataFrame()))

    figure = None
    if not off.empty and not on.empty and not cover.empty:
        off = set_baseline_ice(off, col="md_dt")
        on = set_baseline_ice(on, col="md_dt")
        cover = set_baseline_ice(cover, col="days")
        if not off.empty and not on.empty and not cover.empty:
            figure = _figure_json(stack_ice_figs(off, on, cover))
    else:
        errors.setdefault("ice_history", "Ice history data is unavailable.")

    return {
        "generated_at": _timestamp(),
        "current_year": pd.Timestamp.now().year,
        "figure": figure,
        "errors": errors,
    }


def build_ice_off(comparison_year):
    current_year = pd.Timestamp.now().year
    comparison_year = validate_comparison_year(comparison_year, current_year)
    years = (current_year, comparison_year)
    data, errors = fetch_parallel(
        {
            "ice_extremes": lambda: get_ice_data(kind="extremes"),
            "ice_off_dates": lambda: get_ice_data(kind="off", years=years),
            "snow_depth": lambda: get_snow_depth_data(years=years),
            "air_temperature": lambda: get_air_temp_data(years=years),
        }
    )

    extremes = transform_dates(
        data.get("ice_extremes", pd.DataFrame()), "activity_start_date"
    )
    ice_dates = transform_dates(data.get("ice_off_dates", pd.DataFrame()), "date")
    snow = transform_dates(data.get("snow_depth", pd.DataFrame()), "date")
    air = transform_dates(data.get("air_temperature", pd.DataFrame()), "date")

    figure = None
    if (
        has_columns(snow, ["snow_depth"])
        and has_columns(air, ["avg_temp"])
        and not snow.empty
        and not air.empty
    ):
        figure = _figure_json(
            stack_snow_and_air(
                snow,
                air,
                ice_off_extremes=extremes,
                ice_off_dates=ice_dates,
            )
        )
    else:
        errors.setdefault(
            "ice_off",
            "Snow depth and air temperature data are unavailable.",
        )

    return {
        "generated_at": _timestamp(),
        "current_year": current_year,
        "comparison_year": comparison_year,
        "figure": figure,
        "errors": errors,
    }


def build_lake_turnover():
    data, errors = fetch_parallel(
        {
            "thermocline": get_thermocline_data,
            "lake_surface_temperature": lambda: get_lst_data("daily"),
        }
    )

    thermocline = transform_dates(data.get("thermocline", pd.DataFrame()), "date")
    lake_temperature = data.get("lake_surface_temperature", pd.DataFrame())

    thermocline_figure = None
    if (
        has_columns(thermocline, ["thermocline", "yr", "md_dt"])
        and not thermocline.empty
    ):
        thermocline_figure = _figure_json(plot_thermocline(thermocline))
    else:
        errors.setdefault("thermocline", "Thermocline data is unavailable.")

    lake_temperature_figure = None
    if has_columns(lake_temperature, ["date", "temp"]) and not lake_temperature.empty:
        lake_temperature_figure = _figure_json(
            plot_lst(lake_temperature, measurement_type="daily")
        )
    else:
        errors.setdefault(
            "lake_surface_temperature",
            "Lake surface temperature data is unavailable.",
        )

    return {
        "generated_at": _timestamp(),
        "thermocline_figure": thermocline_figure,
        "lake_temperature_figure": lake_temperature_figure,
        "errors": errors,
    }
