"""
Functions to fetch data from production (API) or local development (RIE) and return the data as pandas DataFrames.
"""

import json
import requests
from json.decoder import JSONDecodeError
import streamlit as st
import pandas as pd


API_BASE = "https://wlcjjmnlwe.execute-api.ca-central-1.amazonaws.com"
RIE_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"


def fetch_df(endpoint: str, params: dict, prod: bool = True) -> pd.DataFrame:
    """
    Fetch data from prod API or local RIE and return as DataFrame.
    """
    if prod:
        r = requests.get(f"{API_BASE}/{endpoint.lstrip('/')}", params=params)
    else:
        r = requests.post(
            RIE_URL, json={"version": "2.0", "queryStringParameters": params}
        )
    r.raise_for_status()
    j = r.json()

    # local rie responses wraps the payload in {'body': '<json string>'} so it needs to be loaded
    payload = j.get("body") if isinstance(j, dict) and "body" in j else j
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except JSONDecodeError:
            payload = {}

    # otherwise treat it as a standard dict
    data = payload.get("data", []) if isinstance(payload, dict) else []
    return pd.DataFrame.from_records(data if isinstance(data, list) else [])


@st.cache_data()
def get_lst_data(measurement_type: str, prod: bool = True) -> pd.DataFrame:
    """
    lake surface temperature: defaults to past 5 years as no date range specified, for September to November.
    measurement_type: 'daily' or 'hourly'
    """
    try:
        return fetch_df(
            "lst",
            {
                # "from": DEFAULT_FROM,
                # "to": DEFAULT_TO,
                "months": "9,10,11",
                "agg": measurement_type.lower(),
            },
            prod=prod,
        )
    except Exception as e:
        st.warning(f"lst fetch failed: {e}")
        return pd.DataFrame()


@st.cache_data()
def get_ice_off_data(
    prod: bool = True, years: list[int] = [], kind: str = "off"
) -> pd.DataFrame:
    """
    ice endpoints:
      - kind='off' requires two years (e.g., [2024, 2025])
      - kind='extremes' ignores years (i.e. it doesn't take it as a parameter)
    years: list of years to filter on (only first two used for 'off' kind)
    If years is not provided, all years are returned (used for baseline analysis)
    """
    try:
        params = {"kind": kind}
        if kind == "off" and years:
            params["years"] = ",".join(
                map(str, years[:2])
            )  # only first two years, if provided. otherwise API defaults to all years, up to the current year
        return fetch_df("ice", params, prod=prod)
    except Exception as e:
        st.warning(f"Ice Fetch Failed: {e}")
        return pd.DataFrame()


@st.cache_data()
def get_snow_depth_data(prod: bool = True, years: list[int] = []) -> pd.DataFrame:
    """
    Fetches snow depth for given two years with months filter, hard coded for February to May.
    years: list of years to filter on (only first two used)
    """
    try:
        return fetch_df(
            "snow_depth",
            {
                "months": "2,3,4,5",
                "years": ",".join(map(str, years[:2])) if years else "",
            },
            prod=prod,
        )
    except Exception as e:
        st.warning(f"Snow Depth Fetch Failed: {e}")
        return pd.DataFrame()


@st.cache_data()
def get_air_temp_data(prod: bool = True, years: list[int] = []) -> pd.DataFrame:
    """
    Fetches daily air temps for given two years with months filter, hard coded for February to May.
    years: list of years to filter on (only first two used)
    """
    try:
        return fetch_df(
            "air_temp",
            {
                "months": "2,3,4,5",
                "years": ",".join(map(str, years[:2])) if years else "",
            },
            prod=prod,
        )
    except Exception as e:
        st.warning(f"Air Temp Fetch Failed: {e}")
        return pd.DataFrame()


@st.cache_data()
def get_thermocline_data(prod: bool = True) -> pd.DataFrame:
    """
    Fetches last 5 years of thermocline data (default;no date range specified) for September to November.
    """
    try:
        return fetch_df(
            "thermocline",
            {"months": "9,10,11"},
            prod=prod,
        )
    except Exception as e:
        st.warning(f"Thermocline Fetch Failed: {e}")
        return pd.DataFrame()
