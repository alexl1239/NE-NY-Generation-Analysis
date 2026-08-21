import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANNUAL_PATH = PROJECT_ROOT / "data" / "processed" / "roe_annual_pilot_2013_2024.csv"
EVENT_PATH = PROJECT_ROOT / "data" / "processed" / "roe_rate_case_events.csv"
SOURCE_PATH = PROJECT_ROOT / "data" / "processed" / "roe_source_register.csv"
SITE_CASE_PATH = PROJECT_ROOT / "site" / "data" / "roe_case_study.csv"
SITE_HTML_PATH = PROJECT_ROOT / "site" / "index.html"
SITE_PANEL_PATH = PROJECT_ROOT / "site" / "panel.js"
SITE_CSS_PATH = PROJECT_ROOT / "site" / "styles.css"


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def annual_row(rows, utility_id, year):
    return next(
        row for row in rows
        if row["utility_id_eia"] == str(utility_id) and row["year"] == str(year)
    )


def test_pilot_has_six_complete_annual_spines():
    rows = read_rows(ANNUAL_PATH)
    assert len(rows) == 72
    assert {(row["utility_id_eia"], row["year"]) for row in rows} == {
        (utility_id, str(year))
        for utility_id in ("4176", "19497", "54913", "11804", "4226", "13511")
        for year in range(2013, 2025)
    }


def test_ownership_change_matches_project_rule():
    rows = read_rows(ANNUAL_PATH)
    assert annual_row(rows, 19497, 2015)["ownership"] == "DOM"
    assert annual_row(rows, 19497, 2016)["ownership"] == "MTC"
    assert {annual_row(rows, 4176, year)["ownership"] for year in range(2013, 2025)} == {"DOM"}
    assert {annual_row(rows, 54913, year)["ownership"] for year in range(2013, 2025)} == {"DOM"}
    assert {annual_row(rows, 11804, year)["ownership"] for year in range(2013, 2025)} == {"MTC"}
    assert {annual_row(rows, 4226, year)["ownership"] for year in range(2013, 2025)} == {"DOM"}
    assert {annual_row(rows, 13511, year)["ownership"] for year in range(2013, 2025)} == {"MTC"}


def test_temporary_and_future_penalties_are_not_confused():
    rows = read_rows(ANNUAL_PATH)
    assert annual_row(rows, 4176, 2015)["effective_authorized_roe"] == "0.0902"
    assert annual_row(rows, 4176, 2016)["effective_authorized_roe"] == "0.0917"
    assert annual_row(rows, 4176, 2021)["effective_authorized_roe"] == "0.0925"
    assert annual_row(rows, 19497, 2021)["effective_authorized_roe"] == "0.091"
    assert annual_row(rows, 19497, 2023)["effective_authorized_roe"] == "0.0863"
    assert annual_row(rows, 54913, 2017)["effective_authorized_roe"] == "0.105"
    assert annual_row(rows, 54913, 2018)["effective_authorized_roe"] == "0.1"
    assert "2018-02-01" in annual_row(rows, 54913, 2018)["annualization_note"]
    assert annual_row(rows, 54913, 2018)["source_ids"] == "S18; S27"
    assert annual_row(rows, 54913, 2023)["effective_authorized_roe"] == "0.098"
    assert annual_row(rows, 11804, 2015)["effective_authorized_roe"] == "0.1035"
    assert annual_row(rows, 11804, 2016)["effective_authorized_roe"] == "0.099"
    assert annual_row(rows, 11804, 2019)["effective_authorized_roe"] == "0.096"
    assert annual_row(rows, 11804, 2024)["effective_authorized_roe"] == "0.0935"
    assert annual_row(rows, 4226, 2013)["effective_authorized_roe"] == "0.1015"
    assert annual_row(rows, 4226, 2014)["effective_authorized_roe"] == "0.092"
    assert annual_row(rows, 4226, 2016)["effective_authorized_roe"] == "0.09"
    assert annual_row(rows, 4226, 2020)["effective_authorized_roe"] == "0.088"
    assert annual_row(rows, 4226, 2023)["effective_authorized_roe"] == "0.0925"
    assert annual_row(rows, 13511, 2013)["effective_authorized_roe"] == "0.1"
    assert annual_row(rows, 13511, 2016)["effective_authorized_roe"] == "0.09"
    assert annual_row(rows, 13511, 2020)["effective_authorized_roe"] == "0.088"
    assert annual_row(rows, 13511, 2023)["effective_authorized_roe"] == "0.092"

    events = read_rows(EVENT_PATH)
    future_orders = [row for row in events if row["event_type"] == "Future penalty order"]
    assert len(future_orders) == 2
    assert {row["applied_to_annual_series"] for row in future_orders} == {"No"}


def test_actual_roe_is_limited_to_documented_ui_years():
    rows = read_rows(ANNUAL_PATH)
    populated = {
        (row["utility_id_eia"], row["year"])
        for row in rows
        if row["actual_earned_roe"]
    }
    assert populated == {("19497", str(year)) for year in range(2017, 2022)}


def test_rate_base_derived_value_is_formula_equivalent():
    rows = read_rows(ANNUAL_PATH)
    ui_2023 = annual_row(rows, 19497, 2023)
    expected = 1105.196 * 0.50 * 0.0863
    assert abs(float(ui_2023["authorized_equity_return_million_usd"]) - expected) < 1e-6
    assert annual_row(rows, 4176, 2023)["authorized_equity_return_million_usd"] == ""


def test_every_referenced_source_id_exists():
    annual = read_rows(ANNUAL_PATH)
    events = read_rows(EVENT_PATH)
    source_ids = {row["source_id"] for row in read_rows(SOURCE_PATH)}

    references = []
    for row in annual:
        references.extend((row["source_ids"], row["actual_roe_source_ids"], row["ownership_source_ids"]))
    references.extend(row["source_ids"] for row in events)

    referenced_ids = {
        source_id.strip()
        for reference in references
        if reference
        for source_id in reference.split(";")
    }
    assert referenced_ids <= source_ids


def test_website_case_study_matches_verified_pilot_and_prices():
    rows = read_rows(SITE_CASE_PATH)
    assert len(rows) == 72
    ui_2024 = annual_row(rows, 19497, 2024)
    clp_2024 = annual_row(rows, 4176, 2024)

    assert ui_2024["ownership"] == "MTC"
    assert ui_2024["effective_authorized_roe"] == "0.0863"
    assert ui_2024["residential_average_price_cents_kwh"] == "34.042707"
    assert clp_2024["ownership"] == "DOM"
    assert clp_2024["effective_authorized_roe"] == "0.0925"
    assert clp_2024["residential_average_price_cents_kwh"] == "28.507537"
    nstar_2024 = annual_row(rows, 54913, 2024)
    meco_2024 = annual_row(rows, 11804, 2024)
    assert nstar_2024["ownership"] == "DOM"
    assert nstar_2024["effective_authorized_roe"] == "0.098"
    assert meco_2024["ownership"] == "MTC"
    assert meco_2024["effective_authorized_roe"] == "0.0935"
    coned_2024 = annual_row(rows, 4226, 2024)
    nyseg_2024 = annual_row(rows, 13511, 2024)
    assert coned_2024["ownership"] == "DOM"
    assert coned_2024["effective_authorized_roe"] == "0.0925"
    assert coned_2024["residential_average_price_cents_kwh"] == "35.66164"
    assert nyseg_2024["ownership"] == "MTC"
    assert nyseg_2024["effective_authorized_roe"] == "0.092"
    assert nyseg_2024["residential_average_price_cents_kwh"] == "18.320617"


def test_website_case_study_does_not_fill_missing_dollar_inputs_with_zero():
    rows = read_rows(SITE_CASE_PATH)
    assert annual_row(rows, 4176, 2024)["approved_rate_base_million_usd"] == ""
    assert annual_row(rows, 4176, 2024)["authorized_equity_return_million_usd"] == ""
    assert annual_row(rows, 19497, 2023)["authorized_equity_return_million_usd"] == "47.689207"


def test_website_roe_points_have_direct_primary_sources():
    rows = read_rows(SITE_CASE_PATH)
    assert all(row["roe_primary_source_title"] for row in rows)
    assert all(row["roe_primary_source_location"] for row in rows)
    assert all(row["roe_primary_source_url"].startswith("https://") for row in rows)
    assert "Final Decision" in annual_row(rows, 19497, 2024)["roe_primary_source_title"]
    ui_2017 = annual_row(rows, 19497, 2017)
    assert ui_2017["roe_primary_source_url"].startswith("https://www.sec.gov/")
    assert "q4cdn.com" not in ui_2017["roe_primary_source_url"]
    assert annual_row(rows, 54913, 2018)["roe_primary_source_url"].startswith("https://www.mass.gov/")
    assert annual_row(rows, 11804, 2019)["roe_primary_source_url"].startswith("https://www.sec.gov/")
    assert annual_row(rows, 4226, 2024)["roe_primary_source_url"].startswith("https://documents.dps.ny.gov/")
    assert annual_row(rows, 13511, 2024)["roe_primary_source_url"].startswith("https://documents.dps.ny.gov/")


def test_website_uses_six_separate_dual_axis_utility_charts():
    html = SITE_HTML_PATH.read_text(encoding="utf-8")
    panel = SITE_PANEL_PATH.read_text(encoding="utf-8")
    css = SITE_CSS_PATH.read_text(encoding="utf-8")

    assert "Each utility stays separate" in html
    assert "full-year average price uses the left axis" in html
    assert "year-end authorized ROE uses the right axis" in html
    assert "Prices are full-year averages and ROE is measured at year-end" in panel
    assert "records.length !== 72" in panel
    assert "for (const utilityId of CT_CASE_STUDY_UTILITY_IDS)" in panel
    assert "buildCtCaseStudyCard(byUtility.get(utilityId), customerClass, priceMaximum)" in panel
    assert "ct-dual-chart__line--price" in css
    assert "ct-dual-chart__line--roe" in css
