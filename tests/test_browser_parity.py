import os
from pathlib import Path

import pytest


BASE_URL = os.getenv("BASE_URL")
APP_VARIANT = os.getenv("APP_VARIANT")
pytestmark = pytest.mark.browser

if not BASE_URL or APP_VARIANT not in {"aws", "streamlit"}:
    pytest.skip(
        "BASE_URL and APP_VARIANT=aws|streamlit are required",
        allow_module_level=True,
    )

from playwright.sync_api import expect, sync_playwright


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120_000)
        yield page
        artifact_dir = Path("build/test-artifacts")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(
            path=artifact_dir / f"{APP_VARIANT}-dashboard.png",
            full_page=True,
        )
        context.close()
        browser.close()


def visible_charts(page):
    return page.locator(".js-plotly-plot:visible")


def test_dashboard_workflow_matches_reference(page):
    expect(
        page.get_by_role("heading", name="ELA Seasonality Dashboard", exact=True)
    ).to_be_visible(timeout=120_000)

    spring = page.get_by_role("tab", name="Ice Off (Spring)", exact=True)
    fall = page.get_by_role("tab", name="Lake Turnover (Fall)", exact=True)
    expect(spring).to_have_attribute("aria-selected", "true")
    expect(visible_charts(page)).to_have_count(2, timeout=120_000)

    comparison = str(pd_year() - 3)
    picker = page.get_by_label("Pick a year", exact=True)
    if APP_VARIANT == "aws":
        picker.select_option(comparison)
    else:
        picker.click()
        page.get_by_role("option", name=comparison, exact=True).click()
    page.get_by_role("button", name="Confirm", exact=True).click()
    expect(visible_charts(page)).to_have_count(2, timeout=120_000)

    fall.click()
    expect(fall).to_have_attribute("aria-selected", "true")
    fall_charts = visible_charts(page)
    fall_charts.first.wait_for(timeout=120_000)
    assert 1 <= fall_charts.count() <= 2

    spring.click()
    expect(spring).to_have_attribute("aria-selected", "true")
    expect(visible_charts(page)).to_have_count(2, timeout=120_000)


def test_visible_figures_contain_data(page):
    page.get_by_role("tab", name="Ice Off (Spring)", exact=True).click()
    charts = visible_charts(page)
    expect(charts).to_have_count(2, timeout=120_000)
    for index in range(2):
        trace_count = charts.nth(index).evaluate(
            "(element) => Array.isArray(element.data) ? element.data.length : 0"
        )
        assert trace_count > 0


def test_current_year_is_not_a_comparison_option(page):
    if APP_VARIANT != "aws":
        pytest.skip("The Streamlit selectbox options are rendered on demand")

    options = page.locator("#comparison-year option").all_text_contents()

    assert str(pd_year()) not in options
    assert str(pd_year() - 1) in options


def test_aws_uses_the_streamlit_brand_logo(page):
    if APP_VARIANT != "aws":
        pytest.skip("The AWS app owns its static logo element")

    logo = page.locator(".brand-logo")
    expect(logo).to_be_visible()
    expect(logo).to_have_attribute(
        "src",
        "/assets/images/iisd-ela-logo-2019.jpg",
    )
    dimensions = logo.evaluate(
        """(element) => ({
            width: element.naturalWidth,
            height: element.naturalHeight,
        })"""
    )
    assert dimensions["width"] > dimensions["height"] * 2


def test_hidden_charts_resize_when_their_tab_is_activated(page):
    if APP_VARIANT != "aws":
        pytest.skip("The AWS app owns tab activation and Plotly resizing")

    spring = page.get_by_role("tab", name="Ice Off (Spring)", exact=True)
    fall = page.get_by_role("tab", name="Lake Turnover (Fall)", exact=True)
    original_viewport = page.viewport_size

    try:
        spring.click()
        expect(visible_charts(page)).to_have_count(2, timeout=120_000)

        for width in (1280, 1000, 900):
            fall.click()
            page.set_viewport_size({"width": width, "height": 900})
            spring.click()
            page.wait_for_function(
                """() => {
                    const charts = [
                        ...document.querySelectorAll(
                            "#spring-panel .js-plotly-plot"
                        ),
                    ];
                    return charts.length === 2 && charts.every((element) => (
                        Math.abs(
                            element._fullLayout.width - element.clientWidth
                        ) <= 1
                    ));
                }""",
                timeout=10_000,
            )
    finally:
        page.set_viewport_size(original_viewport)
        spring.click()


def pd_year():
    from datetime import datetime

    return datetime.now().year
