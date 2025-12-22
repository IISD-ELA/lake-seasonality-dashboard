from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

from iisd_colours import IISD_COLOURS, IISD_SEQ

px.defaults.color_discrete_sequence = IISD_SEQ

FALL_RANGE = ("2000-09-01", "2000-11-17")
WINTER_RANGE = ("2001-02-01", "2001-05-30")
WEEK_MS = 7 * 24 * 60 * 60 * 1000


def get_colour_from_years(
    years, seq=px.defaults.color_discrete_sequence, recent_first=True
):
    """returns a dict mapping years to colors from seq"""
    #  reverse=True puts later years first so they get the first colors in the seq
    yrs = sorted({int(y) for y in years}, reverse=recent_first)
    cmap = {str(y): seq[i % len(seq)] for i, y in enumerate(yrs)}
    return cmap


def add_style_x(fig, start, end, tick0=None, tickangle=45, title=""):
    """shared x-axis style for date axes anchored to a dummy year, created using transform_dates()"""
    fig.update_xaxes(
        title_text=title,
        range=[start, end],
        tick0=tick0 or start,
        dtick=WEEK_MS,
        tickformat="%b-%d",
        tickangle=tickangle,
        showline=True,
        linewidth=1,
        mirror=True,
        ticks="outside",
        ticklen=6,
        tickwidth=1.5,
        tickcolor="black",
    )
    return fig


def add_style_y(fig, title):
    """shared y-axis style for all plots"""
    fig.update_yaxes(
        title_text=title,
        showline=False,
        linewidth=1,
        mirror=True,
        ticks="outside",
        ticklen=4,
    )
    return fig


def add_style_layout(
    fig, *, h=300, w=800, x_title="", y_title="", legend_y=1.4, subtitle=None
):
    """shared layout style for all plots"""
    fig.update_layout(
        height=h,
        width=w,
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend_title="Year",
        legend=dict(
            orientation="h", yanchor="top", y=legend_y, xanchor="center", x=0.5
        ),
        title=dict(
            text="",
            y=0.98,
            x=0.5,
            xanchor="center",
            yanchor="top",
            subtitle=dict(text=subtitle) if subtitle else None,
        ),
        font=dict(size=20, color="black"),
        title_font=dict(size=20, color="black"),
        xaxis_title_font=dict(size=20, color="black"),
        xaxis_tickfont=dict(size=20, color="black"),
        yaxis_title_font=dict(size=20, color="black"),
        yaxis_tickfont=dict(size=20, color="black"),
        hoverlabel_font=dict(size=20, color="black"),
        legend_title_font=dict(size=20, color="black"),
        legend_font=dict(size=20, color="black"),
    )
    return fig


def add_ice_lines(
    fig, *, ice_off_extremes=None, ice_off_dates=None, color_map=None, label_y=1.10
):
    """overlay per-year ice off lines along with earliest and latest dates spanning both subplots"""
    if ice_off_dates is not None and not ice_off_dates.empty:
        for _, r in ice_off_dates.iterrows():
            yr = str(r["yr"])
            col = (color_map or {}).get(yr, "red")
            x = r["season_x"]
            fig.add_vline(
                x=x,
                line_dash="dot",
                line_width=1,
                line_color=col,
                opacity=0.8,
                layer="below",
            )
            fig.add_annotation(
                x=x,
                y=label_y,
                yref="paper",
                text=f"Ice Off<br>{yr}",
                showarrow=False,
                font={"size": 14, "color": col},
                align="center",
            )

    if ice_off_extremes is not None and not ice_off_extremes.empty:
        for t, label in [("min", "Earliest Ice Off"), ("max", "Latest Ice Off")]:
            rec = ice_off_extremes.query("type == @t").iloc[0]
            x = rec["season_x"]
            fig.add_vline(
                x=x,
                line_dash="dot",
                line_width=1,
                line_color=IISD_COLOURS["dark_grey"],
                opacity=0.8,
                layer="below",
            )
            fig.add_annotation(
                x=x,
                y=label_y,
                yref="paper",
                text=f"{label}<br>{int(rec['yr'])}",
                showarrow=False,
                font={"size": 14, "color": IISD_COLOURS["dark_grey"]},
                align="center",
            )
    return fig


def plot_thermocline(res: pd.DataFrame):
    """
    plots thermocline data (thermocline vs date), coloured by year as a line graph
    """
    color_map = get_colour_from_years(res["yr"].unique())
    fig = px.line(
        res.assign(
            thermocline=-res["thermocline"]
        ),  # invert so deeper is more negative
        x="md_dt",
        y="thermocline",
        color="yr",
        color_discrete_map=color_map,
        markers=True,
        hover_data={
            "md_dt": False,
            "date": "|%b %d, %Y",
            "thermocline": ":.1f",
            "yr": True,
        },
        labels={"thermocline": "Depth (m)", "yr": "Year", "date": "Date"},
    )
    fig.update_traces(marker=dict(size=6), line=dict(width=3), opacity=0.8)
    add_style_x(fig, *FALL_RANGE, tick0=FALL_RANGE[0])
    add_style_y(fig, "Thermocline Depth (m)")

    add_style_layout(fig, h=400, w=400, x_title="Date", y_title="Thermocline Depth (m)")
    return fig


def plot_air_temp(res: pd.DataFrame, ice_off_extremes=None, ice_off_dates=None):
    """
    plots average daily air temperature data (temp vs date), coloured by year, as a line graph
    intent is for use with 2 years but will work with any long dataframe with multiple years of data
    """
    # ensure year as str for consistent coloring
    if "yr" not in res.columns:
        res["yr"] = res["date"].dt.year.astype(str)

    color_map = get_colour_from_years(res["yr"].unique())

    fig = px.line(
        res.sort_values("season_x"),
        x="season_x",
        y="avg_temp",
        color="yr",
        markers=True,
        color_discrete_map=color_map,
        hover_data={
            "season_x": False,
            "date": "|%b %d, %Y",
            "avg_temp": ":.1f",
            "yr": True,
        },
        labels={
            "avg_temp": "Average Daily Temperature (°C)",
            "yr": "Year",
            "date": "Date",
        },
    )
    fig.update_traces(marker=dict(size=6), line=dict(width=3), opacity=0.8)

    add_style_x(fig, *WINTER_RANGE, tick0="2001-02-01")
    add_style_y(fig, "Daily Air Temperature (°C)")
    add_style_layout(
        fig, x_title="Month", subtitle=f"{res['yr'].min()} vs {res['yr'].max()}"
    )

    fig.for_each_xaxis(lambda a: a.update(matches=None, showticklabels=True))
    fig.for_each_yaxis(lambda a: a.update(matches=None, showticklabels=True))

    add_ice_lines(
        fig,
        ice_off_extremes=ice_off_extremes,
        ice_off_dates=ice_off_dates,
        color_map=color_map,
        label_y=1.10,
    )

    return fig


def plot_snow_depth(res: pd.DataFrame, ice_off_extremes=None, ice_off_dates=None):
    """
    - plots snow depth data (depth vs date), coloured by year as a grouped bar chart
    - intent is for use with 2 years but will work with any long dataframe with multiple years of data
    - may look messy as it's a grouped barchart
    """

    if "yr" not in res.columns:
        res["yr"] = res["date"].dt.year.astype(str)

    color_map = get_colour_from_years(res["yr"].unique())

    fig = px.bar(
        res,
        x="season_x",
        y="snow_depth",
        color="yr",
        barmode="group",
        color_discrete_map=color_map,
        hover_data={
            "season_x": False,
            "date": "|%b %d, %Y",
            "snow_depth": ":.1f",
            "yr": True,
        },
        labels={"snow_depth": "Snow Depth (cm)", "yr": "Year", "date": "Date"},
    )
    add_style_x(fig, *WINTER_RANGE, tick0="2001-02-01")
    add_style_y(fig, "Snow Depth (cm)")
    add_style_layout(
        fig, x_title="Month", subtitle=f"{res['yr'].min()} vs {res['yr'].max()}"
    )
    fig.for_each_xaxis(lambda a: a.update(matches=None, showticklabels=True))
    fig.for_each_yaxis(lambda a: a.update(matches=None, showticklabels=True))

    add_ice_lines(
        fig,
        ice_off_extremes=ice_off_extremes,
        ice_off_dates=ice_off_dates,
        color_map=color_map,
        label_y=1.10,
    )
    return fig


def plot_lst(res: pd.DataFrame, measurement_type: str):
    """
    plots lake surface tep data (temp vs date), coloured by year, as a line graph
    intent is for use with 2 years but will work with any long dataframe with multiple years of data
    """
    # normalize x to md_dt based on requested granularity
    res = res.copy()
    res["date"] = pd.to_datetime(res["date"])
    if measurement_type.lower() == "hourly":
        res["md_dt"] = pd.to_datetime(
            "2000-" + res["date"].dt.strftime("%m-%d, %H:%M:%S"),
            format="%Y-%m-%d, %H:%M:%S",
        )
    else:
        res["md_dt"] = pd.to_datetime(
            "2000-" + res["date"].dt.strftime("%m-%d"), format="%Y-%m-%d"
        )
    if "yr" not in res.columns:
        res["yr"] = res["date"].dt.year.astype(str)

    color_map = get_colour_from_years(res["yr"].unique())
    fig = px.line(
        res,
        x="md_dt",
        y="temp",
        color="yr",
        color_discrete_map=color_map,
        markers=True,
        hover_data={
            "md_dt": False,
            "date": "|%b %d, %Y",
            "temp": ":.1f",
            "yr": True,
        },
        labels={
            "temp": "Daily Lake Surface Temperature (°C)",
            "yr": "Year",
            "date": "Date",
        },
    )
    fig.update_traces(marker=dict(size=6), line=dict(width=3), opacity=0.8)
    add_style_x(fig, *FALL_RANGE, tick0=FALL_RANGE[0])

    fig.update_yaxes(
        zeroline=False,
        tickformat=".2f",
        mirror="allticks",
        ticks="outside",
        ticklen=6,
        tickwidth=1.5,
        tickcolor="black",
    )

    add_style_layout(
        fig, h=400, w=400, x_title="Date", y_title="Lake Surface Temperature (°C)"
    )
    return fig


def stack_ice_figs(off_df, cover_df, on_df):
    """
    - creates a vertically stacked dataframe given three datafraes, one for each of ice off dates, ice on dates, and ice duration dates
    """

    def prep(df):
        d = df.copy().sort_values("yr")
        d["sign"] = (
            d["days_from_baseline"].lt(0).map({True: "negative", False: "positive"})
        )
        return d

    def add_row(d, row):
        for sign, sub in d.groupby("sign"):
            fig.add_trace(
                go.Bar(
                    x=sub["yr"],
                    y=sub["days_from_baseline"],
                    name=sign,
                    marker_color=color_map[sign],
                    showlegend=(row == 1),
                    hovertemplate="Year: %{x}<br>Days from Mean: %{y}",
                ),
                row=row,
                col=1,
            )
        fig.update_yaxes(
            title_text="Days From Mean",
            row=row,
            col=1,
            showline=True,
            linewidth=1,
            mirror=True,
            ticks="outside",
            ticklen=4,
            title_font=dict(size=20, color="black"),
            tickfont=dict(size=20, color="black"),
        )

    off = prep(off_df)
    cover = prep(cover_df)
    on = prep(on_df)

    color_map = {
        "negative": IISD_COLOURS["light_blue"],
        "positive": IISD_COLOURS["navy_blue"],
    }

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.33, 0.33, 0.34],
        subplot_titles=("Ice Off", "Ice Cover Duration", "Ice On"),
    )

    add_row(off, 1)
    add_row(on, 3)
    add_row(cover, 2)

    off["yr"] = off["yr"].astype(int)
    min_year = int(off["yr"].min())
    tick0 = (min_year // 5) * 5  # first 5-year boundary at/before min

    # single x at bottom
    fig.update_xaxes(
        tick0=tick0,
        dtick=5,
        tickangle=45,
        showline=True,
        linewidth=1,
        mirror=False,
        ticks="outside",
        row=3,
        col=1,
        type="linear",
        ticklen=6,
        tickwidth=1.5,
        tickcolor="black",
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )
    fig.update_xaxes(
        showticklabels=False, row=1, col=1, showline=False, mirror=False, type="linear"
    )
    fig.update_xaxes(
        showticklabels=False, row=2, col=1, type="linear", showline=False, mirror=False
    )
    fig.update_yaxes(
        showline=False,
        mirror=False,
    )
    fig.update_layout(
        height=720,
        width=600,
        title="",
        margin=dict(l=60, r=20, t=60, b=50),
        showlegend=False,
        font=dict(size=20, color="black"),
        title_font=dict(size=20, color="black"),
        xaxis_title_font=dict(size=20, color="black"),
        xaxis_tickfont=dict(size=20, color="black"),
        yaxis_title_font=dict(size=20, color="black"),
        yaxis_tickfont=dict(size=20, color="black"),
        hoverlabel_font=dict(size=20, color="black"),
        title_subtitle_font=dict(size=20, color="black"),
    )

    fig.update_annotations(font_size=20)  # subtitles are annotations apparently

    return fig


def stack_snow_and_air(snow_df, air_df, ice_off_extremes=None, ice_off_dates=None):

    fig_snow = plot_snow_depth(
        snow_df, ice_off_extremes=ice_off_extremes, ice_off_dates=ice_off_dates
    )
    fig_air = plot_air_temp(
        air_df, ice_off_extremes=ice_off_extremes, ice_off_dates=ice_off_dates
    )

    combo = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07, row_heights=[0.5, 0.5]
    )
    # add traces
    for tr in fig_snow.data:
        combo.add_trace(tr, row=1, col=1)
    for tr in fig_air.data:
        tr.showlegend = False
        combo.add_trace(tr, row=2, col=1)

    # x ranges + ticks on both rows
    combo.update_xaxes(
        range=list(WINTER_RANGE),
        row=1,
        col=1,
        showticklabels=True,
        matches=None,
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )
    # move to the top
    # combo.update_xaxes(side="top", row=1, col=1)
    # combo.update_layout(margin=dict(t=120))

    # only show on the bottom
    combo.update_xaxes(showticklabels=False, row=1, col=1)
    combo.update_xaxes(showticklabels=True, row=2, col=1)

    combo.update_xaxes(
        range=list(WINTER_RANGE),
        row=2,
        col=1,
        showticklabels=True,
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )
    combo.update_xaxes(
        tick0=WINTER_RANGE[0],
        dtick=WEEK_MS,
        tickformat="%b-%d",
        showline=True,
        linewidth=1,
        mirror=True,
        ticks="outside",
        ticklen=6,
        tickwidth=1.5,
        tickcolor="black",
        tickangle=45,
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )
    # y axes titles
    combo.update_yaxes(
        title_text="Snow Depth (cm)",
        row=1,
        col=1,
        showline=False,
        linewidth=1,
        mirror=False,
        ticks="outside",
        ticklen=4,
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )
    combo.update_yaxes(
        title_text="Daily Air Temperature (°c)",
        row=2,
        col=1,
        showline=False,
        linewidth=1,
        mirror=False,
        ticks="outside",
        ticklen=4,
        title_font=dict(size=20, color="black"),
        tickfont=dict(size=20, color="black"),
    )

    combo.update_layout(
        height=650,
        width=900,
        title_text="",
        margin=dict(t=90, b=40, l=60, r=20),
        legend=dict(orientation="h", x=0.5, y=1.08, xanchor="center", yanchor="bottom"),
        font=dict(size=20, color="black"),
        title_font=dict(size=20, color="black"),
        xaxis_title_font=dict(size=20, color="black"),
        xaxis_tickfont=dict(size=20, color="black"),
        yaxis_title_font=dict(size=20, color="black"),
        yaxis_tickfont=dict(size=20, color="black"),
        hoverlabel_font=dict(size=20, color="black"),
        legend_font=dict(size=20, color="black"),
    )

    # re-add ice overlays once to span both subplots
    years = sorted(
        set(map(str, pd.concat([snow_df["yr"], air_df["yr"]]).astype(int).unique()))
    )
    color_map = get_colour_from_years(years)
    add_ice_lines(
        combo,
        ice_off_extremes=ice_off_extremes,
        ice_off_dates=ice_off_dates,
        color_map=color_map,
        label_y=1.01,
    )
    combo.update_annotations(font_size=18)
    return combo


def add_snow_dates(df, date_col):
    """adds season_x and season_label columns to df based on date_col"""
    # build a dummy-year datetime col for plotting: "season_x"
    #   nov dec -> year 2000
    #   jan–may -> year 2001 (shifted so the axis is continuous)

    df["season_start"] = df[date_col].dt.year.where(
        df[date_col].dt.month >= 11, df[date_col].dt.year - 1
    )
    df["season_label"] = (
        df["season_start"].astype(str)
        + "/"
        + (df["season_start"] + 1).astype(str).str[-2:]
    )

    md2000 = pd.to_datetime("2000-" + df[date_col].dt.strftime("%m-%d"))
    df["season_x"] = md2000.mask(md2000.dt.month <= 5, md2000 + pd.DateOffset(years=1))

    return df
