"""Browser E2E scenarios for the report UI (Chromium / Playwright)."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.ui


def test_nav_smoke(page: Page, live_server: str):
    page.goto(f"{live_server}/")
    expect(page.get_by_role("heading", name="Overview")).to_be_visible()
    page.get_by_role("link", name="Runs", exact=True).click()
    expect(page.get_by_role("heading", name=re.compile(r"Runs", re.I))).to_be_visible()
    page.get_by_role("link", name="New run").first.click()
    expect(page.locator("#suite_id")).to_be_visible()
    page.get_by_role("link", name="Tool docs").click()
    expect(page.get_by_role("heading", name=re.compile(r"Tool", re.I))).to_be_visible()


def test_overview_charts_stub(page: Page, live_server: str):
    page.goto(f"{live_server}/")
    expect(page.locator("#chart-severity")).to_have_attribute("data-charted", "1", timeout=10_000)
    expect(page.locator("#chart-hotspots")).to_have_attribute("data-charted", "1")
    expect(page.locator("#chart-trend")).to_have_attribute("data-charted", "1")


def test_findings_filter_and_expand(page: Page, live_server: str):
    page.goto(f"{live_server}/")
    page.get_by_role("link", name=re.compile(r"View findings", re.I)).click()
    expect(page.get_by_text("unused import")).to_be_visible()
    expect(page.get_by_text("line too long")).to_be_visible()

    page.locator("#rule_id").select_option("F401")
    page.get_by_role("button", name=re.compile(r"Apply|Filter", re.I)).click()
    expect(page.get_by_text("unused import")).to_be_visible()
    expect(page.get_by_text("line too long")).to_have_count(0)

    row = page.locator(".finding-summary").first
    row.click()
    expect(row).to_have_class(re.compile(r"finding-expanded"))
    expect(page.get_by_role("link", name="Rule docs")).to_be_visible()


def test_new_run_suite_filters_checks(page: Page, live_server: str):
    page.goto(f"{live_server}/runs/new")
    suite = page.locator("#suite_id")
    check = page.locator("#check")
    expect(suite).to_be_visible()
    assert suite.locator("option").count() >= 2
    select_alternate_suite(suite)
    selected = suite.input_value()
    for option in enabled_check_options(check):
        suite_attr = option.get_attribute("data-suite")
        if suite_attr:
            assert suite_attr == selected


def select_alternate_suite(suite) -> None:
    first = suite.input_value()
    options = suite.locator("option")
    for i in range(options.count()):
        value = options.nth(i).get_attribute("value") or ""
        if value and value != first:
            suite.select_option(value)
            return


def enabled_check_options(check):
    return [
        check.locator("option").nth(i)
        for i in range(check.locator("option").count())
        if not check.locator("option").nth(i).is_disabled()
    ]


def fill_branch(page: Page, value: str = "main") -> None:
    branch = page.locator("#branch")
    if branch.evaluate("el => el.tagName") == "SELECT":
        branch.select_option(index=0)
    else:
        branch.fill(value)


def test_new_run_shows_progress(page: Page, live_server: str):
    page.goto(f"{live_server}/runs/new")
    fill_branch(page)
    page.get_by_role("button", name=re.compile(r"Start", re.I)).click()
    expect(page.locator("text=Status:")).to_be_visible(timeout=10_000)
    expect(page.get_by_text(re.compile(r"Installing|checks ", re.I))).to_be_visible()


def test_cancel_running_run(page: Page, cancel_live_server: str):
    page.goto(f"{cancel_live_server}/runs/new")
    fill_branch(page)
    page.get_by_role("button", name=re.compile(r"Start", re.I)).click()
    cancel = page.get_by_role("button", name="Cancel")
    expect(cancel).to_be_visible(timeout=10_000)
    cancel.click()
    expect(page.get_by_text(re.compile(r"cancelled", re.I))).to_be_visible(timeout=15_000)


def test_new_fixed_page(page: Page, live_server: str):
    page.goto(f"{live_server}/")
    link = page.locator('a[href*="/new-code"]')
    expect(link).to_be_visible()
    link.click()
    expect(page.get_by_role("heading", name="New / Fixed")).to_be_visible()
    expect(page.get_by_text("Fixed vs baseline")).to_be_visible()
    expect(page.get_by_text("unused variable")).to_be_visible()
