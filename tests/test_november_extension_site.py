import csv
import json
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = PROJECT_ROOT / "site" / "data"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


class NovemberExtensionSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.processed_prices = read_csv(
            PROJECT_ROOT / "data/processed/utility_price_history_2001_2024.csv"
        )
        cls.processed_events = read_csv(
            PROJECT_ROOT
            / "data/processed/ownership_research_design_events_2001_2024.csv"
        )
        cls.processed_controls = read_csv(
            PROJECT_ROOT
            / "data/processed/ownership_research_design_control_pool_2001_2024.csv"
        )
        cls.site_prices = read_csv(
            SITE_DATA / "november_extension_price_history.csv"
        )
        cls.site_events = read_csv(
            SITE_DATA / "november_extension_research_design.csv"
        )
        cls.site_controls = read_csv(
            SITE_DATA / "november_extension_control_pool.csv"
        )

    def test_page_exports_the_full_2001_2024_period(self) -> None:
        self.assertEqual(len(self.site_prices), 42 * 24 * 3)
        self.assertEqual(
            {int(row["year"]) for row in self.site_prices}, set(range(2001, 2025))
        )
        self.assertEqual(
            sum(bool(row["average_price_cents_kwh"]) for row in self.site_prices),
            2903,
        )
        self.assertEqual(
            {row["panel_id"] for row in self.site_prices},
            {row["panel_id"] for row in self.processed_prices},
        )

    def test_price_export_is_an_exact_filtered_copy(self) -> None:
        fields = list(self.site_prices[0])
        expected = [
            {field: row[field] for field in fields}
            for row in self.processed_prices
            if int(row["year"]) <= 2024
        ]
        self.assertEqual(self.site_prices, expected)

    def test_event_and_control_exports_stay_in_the_historical_period(self) -> None:
        self.assertEqual(len(self.site_events), 27)
        self.assertEqual(
            len({row["event_id"] for row in self.site_events}),
            9,
        )
        self.assertTrue(
            all(int(row["year_end_treatment_year"]) <= 2024 for row in self.site_events)
        )
        self.assertEqual(
            Counter(row["phase6_window_role"] for row in self.site_events),
            {
                "primary_4_year_window": 15,
                "sensitivity_2_year_window": 3,
                "excluded_insufficient_price_window": 7,
                "excluded_extremely_thin_customer_base": 2,
            },
        )
        self.assertEqual(len(self.site_controls), 18 * 42)
        self.assertEqual(
            {row["event_id"] for row in self.site_controls},
            {
                row["event_id"]
                for row in self.site_events
                if row["phase6_window_role"]
                in {"primary_4_year_window", "sensitivity_2_year_window"}
            },
        )

    def test_browser_payload_metadata_matches_the_extension(self) -> None:
        price_payload = json.loads(
            (SITE_DATA / "november_extension_price_history.json").read_text(
                encoding="utf-8"
            )
        )
        design_payload = json.loads(
            (SITE_DATA / "november_extension_research_design.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(price_payload["metadata"]["year_start"], 2001)
        self.assertEqual(price_payload["metadata"]["year_end"], 2024)
        self.assertEqual(price_payload["metadata"]["published_price_count"], 2903)
        self.assertEqual(len(price_payload["records"]), 3024)
        self.assertEqual(price_payload["metadata"]["constant_dollar_year"], 2024)
        cpi = price_payload["metadata"]["cpi_u_annual_2013_100"]
        self.assertEqual(set(map(int, cpi)), set(range(2001, 2025)))
        self.assertEqual(cpi["2013"], 100.0)
        self.assertEqual(cpi["2024"], 134.655)
        self.assertEqual(design_payload["metadata"]["ownership_change_count"], 9)
        self.assertEqual(design_payload["metadata"]["primary_rows"], 15)
        self.assertEqual(design_payload["metadata"]["sensitivity_rows"], 3)
        self.assertFalse(design_payload["metadata"]["causal_estimates_included"])

    def test_page_is_a_companion_not_a_duplicate_of_the_original_panel(self) -> None:
        html = (PROJECT_ROOT / "site/november-data-extension.html").read_text(
            encoding="utf-8"
        )
        javascript = (PROJECT_ROOT / "site/november-data-extension.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("Extended historical data · 2001–2024", html)
        self.assertIn("same 42 utilities", html)
        self.assertIn('id="extension-price-basis"', html)
        self.assertIn("Inflation-adjusted 2024 cents", html)
        self.assertIn("report a causal estimate", html)
        self.assertIn("Annual median prices", html)
        self.assertNotIn("extension-stat-grid", html)
        self.assertNotIn("extension-history-table", html)
        self.assertNotIn("extension-event-table", html)
        self.assertIn("pricePayload.metadata.year_end", javascript)
        self.assertIn("cpiU[constantDollarYear] / cpiU[year]", javascript)

    def test_utility_points_show_exact_details_without_a_large_table(self) -> None:
        html = (PROJECT_ROOT / "site/november-data-extension.html").read_text(
            encoding="utf-8"
        )
        javascript = (PROJECT_ROOT / "site/november-data-extension.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="extension-point-detail"', html)
        self.assertIn("Bundled customers", javascript)
        self.assertIn("data-history-year", javascript)
        self.assertIn('point.addEventListener("click", selectPoint)', javascript)
        self.assertIn('point.addEventListener("focus", selectPoint)', javascript)
        self.assertNotIn('id="extension-history-body"', html)

    def test_group_median_points_have_interactive_details(self) -> None:
        html = (PROJECT_ROOT / "site/november-data-extension.html").read_text(
            encoding="utf-8"
        )
        javascript = (PROJECT_ROOT / "site/november-data-extension.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="extension-trend-detail"', html)
        self.assertNotIn('id="extension-trend-summary"', html)
        self.assertIn("data-trend-key", javascript)
        self.assertIn("Utilities included", javascript)
        self.assertIn("Observed range", javascript)
        self.assertIn('chartPoint.addEventListener("pointerenter", selectPoint)', javascript)

    def test_each_historical_change_has_a_short_sourced_explanation(self) -> None:
        html = (PROJECT_ROOT / "site/november-data-extension.html").read_text(
            encoding="utf-8"
        )
        for utility in (
            "Versant Power lineage (Bangor Hydro)",
            "Niagara Mohawk",
            "Green Mountain Power",
            "Central Maine Power",
            "NYSEG",
            "Rochester Gas &amp; Electric",
            "Central Hudson",
            "United Illuminating",
            "Rhode Island Energy",
        ):
            self.assertIn(utility, html)
        self.assertEqual(html.count(">Source</a>"), 9)

    def test_original_pages_link_to_the_companion_page(self) -> None:
        for page in (
            "index.html",
            "price-model.html",
            "reliability-panel-model.html",
        ):
            html = (PROJECT_ROOT / "site" / page).read_text(encoding="utf-8")
            self.assertIn(
                '<a href="november-data-extension.html">Extended historical data</a>',
                html,
            )


if __name__ == "__main__":
    unittest.main()
