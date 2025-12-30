import streamlit as st
import pandas as pd

from get_data import (
    get_lst_data,
    get_air_temp_data,
    get_thermocline_data,
    get_ice_off_data,
    get_snow_depth_data,
)

from plot import (
    plot_lst,
    plot_thermocline,
    plot_air_temp,
    plot_snow_depth,
    add_snow_dates,
    stack_snow_and_air,
    # plot_ice_baselines,
    stack_ice_figs,
)

from pathlib import Path


def inject_css(path: str):
    css = Path(path).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


inject_css("static/styles.css")

# doesn't work or overriden by other defaults?
# import plotly.graph_objects as go
# import plotly.io as pio

# my_template = go.layout.Template()

# my_template.layout.font = dict(
#     size=20,
#     color="black"
# )


# my_template.layout.xaxis = dict(
#     title_font=dict(
#         size=20,
#         color="black"
#     ),
#     tickfont=dict(
#         size=20,
#         color="black"
#     )
# )

# my_template.layout.yaxis = dict(
#     title_font=dict(
#         size=20,
#         color="black"
#     ),
#     tickfont=dict(
#         size=20,
#         color="black"
#     )
# )

# my_template.layout.legend = dict(
#     font=dict(
#         size=20,
#         color="black"
#     )
# )


# my_template.layout.hoverlabel = dict(
#     font=dict(
#         size=20,
#         color="black"
#     )
# )

# pio.templates.default = my_template
# ---- end brand stuff ------


st.set_page_config(page_title="ELA Seasonality Dashboard", layout="wide")

st.title("ELA Seasonality Dashboard")
st.logo("static/images/iisd-ela-logo-2019 1.jpg", size="large")


# NOTE: For future development and to understand what the data looks like, it would be helpful to set the value of DEBUG to True
# so one can see the input data to the plotting functions 
# DEBUG = st.toggle("Debug Mode", value=False)
DEBUG = False  # hard disable for prod


# --- helper functions -----
def transform_dates(df, date_col="date"):
    """adds md (month day), md_dt (dummified month-day for plotting), yr columns to df based on date_col"""

    df[date_col] = pd.to_datetime(df[date_col])
    df["md"] = df[date_col].dt.strftime("%m-%d")
    df["md_dt"] = pd.to_datetime("2000-" + df["md"], format="%Y-%m-%d")
    df["yr"] = pd.to_datetime(df[date_col].dt.year).astype("int").astype("str")
    df = add_snow_dates(df, date_col)

    return df


def set_baseline_ice(df, col="md_dt", type="mean"):
    """adds days_from_baseline column to df based on md_dt baseline (mean or median)"""
    if type == "mean":
        df["baseline"] = df[col].mean()
    elif type == "median":
        df["baseline"] = df[col].median()

    if col == "md_dt":
        out = df.assign(days_from_baseline=lambda d: (d[col] - d["baseline"]).dt.days)
    else:
        out = df.assign(
            days_from_baseline=lambda d: (d[col] - d["baseline"]).astype("int")
        )
    return out


def transform_cover(df):
    """compuets difference between start and end daes for ice cover duraion"""
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    df["days"] = (df["end_date"] - df["start_date"]).dt.days
    df["yr"] = (df["start_date"]).dt.year
    df = df.sort_values("yr")

    return df


######################################################################################################################################################


"""
Author: Delvin So (dso@iisd-ela.org)

### About

This dashboard provides visualizations of ice off dates, lake turnover, air temperature, snow depth, and thermocline data collected at the ELA to help researchers and staff plan their field activities and understand seasonal patterns in the lakes.

Specifically, knowing when ice off occurs on the lakes is important for planning the start of the field season, whereas lake turnover is important for planning fall sampling and for scientific research. 

**All data presented is collected from LA 239 at IISD-ELA.**
"""



# expander = st.expander("Are data updates automatic?")

st.write("""
    ### Data Updates
    The dashboard is updated automatically with the database, meaning:

    - Snow depth and air temperature figure will change to 2026 as the year to be compared against automatically in the new year. Note this will mean that although it is 2026, the figure will be missing the data until it is uploaded to the database. This functionality is intended and was discussed with C. Hay.
    - Similarly, the ice date analysis figure will automatically include the 2026 data when the database is updated with the corresponding data.
    - Lastly, thermocline and lake surface temperature is configured to automatically use the latest 5 years of data, so again, when the database is updated then so will the dashboard. 
    """)

ice_off_tab, lake_turnover_tab = st.tabs(["Ice Off (Spring)", "Lake Turnover (Fall)"])

# static data
ice_off_extremes = get_ice_off_data(kind="extremes")
ice_off_extremes = transform_dates(ice_off_extremes, "activity_start_date")


with ice_off_tab:

    cols = st.columns([3, 2])

    with cols[0].container(border=True, height="stretch"):
        "### Snow Depth and Air Temperature Comparisons"

        spacer_cols = st.columns([3, 1], gap="small")
        with spacer_cols[0]:
            f"The figure below shows snow depth and air temperature comparisons for a selected year (via the dropdown box) against the current year {pd.Timestamp.now().year}. "
            "If the data is not yet available for the current year, then the figure will ONLY show the comparison year selected."
        years = list(range(2000, 2026))

        TEST_WITH_NEXT_YEAR_AS_CURRENT_YEAR = False # if set to False, it will use the default value of this year as the year to be compared against
        # TEST_WITH_NEXT_YEAR_AS_CURRENT_YEAR = st.toggle(
        #     "Toggle to test with 2026 as the current year, otherwise 2025", value=True
        # )
        # defaults
        if TEST_WITH_NEXT_YEAR_AS_CURRENT_YEAR:
            st.session_state["years_confirmed"] = [
                pd.Timestamp.now().year,
                pd.Timestamp.now().year + 1,
            ]  # simulate as we're in 2026
        else:
            st.session_state["years_confirmed"] = [
                pd.Timestamp.now().year - 1,
                pd.Timestamp.now().year,
            ]  # current year
        with spacer_cols[-1]:
            with st.form("year_picker"):

                chosen = st.selectbox(
                    label="Pick a year",
                    options=years,
                    index=len(years) - 2,  # the previous year
                )
                submit = st.form_submit_button("Confirm", type="primary")

        if submit:
            if TEST_WITH_NEXT_YEAR_AS_CURRENT_YEAR:
                st.session_state["years_confirmed"] = (pd.Timestamp.now().year + 1, chosen)

            else:
                st.session_state["years_confirmed"] = (pd.Timestamp.now().year, chosen)

        ice_off_dates = get_ice_off_data(years=st.session_state["years_confirmed"])
        ice_off_dates = transform_dates(ice_off_dates, "date")

        snow = get_snow_depth_data(years=st.session_state["years_confirmed"])
        air = get_air_temp_data(years=st.session_state["years_confirmed"])

        snow = transform_dates(snow)
        air = transform_dates(air)

        fig = stack_snow_and_air(snow, air, ice_off_extremes, ice_off_dates)

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with cols[1].container(border=True, height="stretch"):
        "### Ice Dates and Cover Analysis"

        f"The following figure shows the days from mean for ice off dates, ice cover duration, and ice on dates from 1969 to {pd.Timestamp.now().year}, if the data is available."

        off = transform_dates(get_ice_off_data(kind="off"), "date")
        cover = transform_cover(get_ice_off_data(kind="cover"))
        on = transform_dates(get_ice_off_data(kind="on"), "date")

        if DEBUG:
            st.dataframe(off.head(5))
            st.dataframe(cover.head(5))
            st.dataframe(on.head(5))

        off = set_baseline_ice(off, type="mean", col="md_dt")
        cover = set_baseline_ice(cover, type="mean", col="days")
        on = set_baseline_ice(on, type="mean", col="md_dt")

        if DEBUG:
            st.dataframe(off.head(5))
            st.dataframe(cover.head(5))
            st.dataframe(on.head(5))

        fig = stack_ice_figs(off, on, cover)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


with lake_turnover_tab:
    cols = st.columns([2, 3])

    with cols[0].container(border=True, height="stretch"):

        "#### Thermocline (m)"

        tcl = get_thermocline_data(prod=True)
        tcl = transform_dates(tcl, "date")

        if DEBUG:
            st.dataframe(tcl.sort_values("md").head(5))

        fig = plot_thermocline(tcl)

        st.plotly_chart(fig, use_container_width=True)

    with cols[1].container(border=True, height="stretch"):

        st.markdown("#### Lake Surface Temperature (°C)")

        measurement_type = "daily"
        dat = get_lst_data(measurement_type.lower())

        fig = plot_lst(res=dat, measurement_type=measurement_type.lower())

        st.plotly_chart(fig, use_container_width=True)
