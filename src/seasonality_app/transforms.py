"""Data transformations shared by the AWS API endpoints."""

import pandas as pd

from plot import add_snow_dates


def has_columns(df, columns):
    return isinstance(df, pd.DataFrame) and all(column in df.columns for column in columns)


def transform_dates(df, date_col="date"):
    """Add plotting date, month-day, and year columns."""
    if not has_columns(df, [date_col]) or df.empty:
        return pd.DataFrame()

    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result = result[result[date_col].notna()].copy()
    if result.empty:
        return result

    result["md"] = result[date_col].dt.strftime("%m-%d")
    result["md_dt"] = pd.to_datetime("2000-" + result["md"], format="%Y-%m-%d")
    result["yr"] = result[date_col].dt.year.astype("int").astype("str")
    return add_snow_dates(result, date_col)


def set_baseline_ice(df, col="md_dt", baseline_type="mean"):
    """Add days from the mean or median baseline."""
    if not has_columns(df, [col]) or df.empty:
        return pd.DataFrame()
    if baseline_type not in {"mean", "median"}:
        raise ValueError("baseline_type must be 'mean' or 'median'")

    result = df.copy()
    result["baseline"] = (
        result[col].mean() if baseline_type == "mean" else result[col].median()
    )
    if col == "md_dt":
        return result.assign(
            days_from_baseline=lambda data: (
                data[col] - data["baseline"]
            ).dt.days
        )
    return result.assign(
        days_from_baseline=lambda data: (
            data[col] - data["baseline"]
        ).astype("int")
    )


def transform_cover(df):
    """Compute ice-cover duration and observation year."""
    if not has_columns(df, ["start_date", "end_date"]) or df.empty:
        return pd.DataFrame()

    result = df.copy()
    result["start_date"] = pd.to_datetime(result["start_date"], errors="coerce")
    result["end_date"] = pd.to_datetime(result["end_date"], errors="coerce")
    result = result[
        result["start_date"].notna() & result["end_date"].notna()
    ].copy()
    if result.empty:
        return result

    result["days"] = (result["end_date"] - result["start_date"]).dt.days
    result["yr"] = result["start_date"].dt.year
    return result.sort_values("yr")
