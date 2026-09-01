import csv
import json
import re
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PANEL_CSV = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
SITE_CSV = PROJECT_ROOT / "site" / "data" / "utility_price_panel.csv"
SITE_JSON = PROJECT_ROOT / "site" / "data" / "utility_price_panel.json"
SITE_JS = PROJECT_ROOT / "site" / "data" / "utility_price_panel.js"
SECTORS = {
    "residential": 6,
    "commercial": 7,
    "industrial": 8,
}


class TestUtilityPricePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with PANEL_CSV.open(newline="") as source:
            cls.rows = list(csv.DictReader(source))

    def test_panel_is_balanced_30_by_12(self):
        self.assertEqual(len(self.rows), 360)
        self.assertEqual(len({row["panel_id"] for row in self.rows}), 30)
        self.assertEqual({int(row["year"]) for row in self.rows}, set(range(2013, 2025)))
        counts = Counter(row["panel_id"] for row in self.rows)
        self.assertEqual(set(counts.values()), {12})
        self.assertEqual(
            len({(row["panel_id"], row["year"]) for row in self.rows}),
            360,
        )

    def test_only_current_three_ownership_categories_are_used(self):
        self.assertEqual({row["ownership"] for row in self.rows}, {"MTC", "DOM", "COOP"})
        counts_2024 = Counter(
            row["ownership"] for row in self.rows if row["year"] == "2024"
        )
        self.assertEqual(counts_2024, {"MTC": 10, "DOM": 10, "COOP": 10})

    def test_time_varying_ownership_is_coded_by_year(self):
        ownership = {
            (int(row["utility_id_eia"]), int(row["year"])): row["ownership"]
            for row in self.rows
        }
        self.assertEqual(ownership[(19497, 2015)], "DOM")
        self.assertEqual(ownership[(19497, 2016)], "MTC")
        self.assertEqual(ownership[(13214, 2021)], "MTC")
        self.assertEqual(ownership[(13214, 2022)], "DOM")

    def test_ownership_changes_have_official_history_sources(self):
        latest = {
            int(row["utility_id_eia"]): row
            for row in self.rows
            if row["year"] == "2024"
        }
        self.assertTrue(
            latest[19497]["ownership_history_source_url"].startswith("https://www.sec.gov/")
        )
        self.assertTrue(
            latest[13214]["ownership_history_source_url"].startswith(
                "https://investors.pplweb.com/"
            )
        )

    def test_published_sector_price_availability_and_source_labels(self):
        available = {}
        for sector, table_number in SECTORS.items():
            count = 0
            for row in self.rows:
                price = row[f"{sector}_average_price_cents_kwh"]
                expected_table = (
                    f"Table {table_number}: Utility Bundled Retail Sales - "
                    f"{sector.title()}"
                )
                self.assertEqual(row[f"{sector}_source_table"], expected_table)
                self.assertTrue(row["source_url"].startswith("https://www.eia.gov/"))
                if price:
                    count += 1
                    self.assertEqual(row[f"{sector}_source_status"], "Reported")
                    self.assertGreater(float(price), 0)
                    self.assertGreater(int(row[f"bundled_{sector}_customers"]), 0)
                else:
                    self.assertEqual(row[f"{sector}_source_status"], "Not reported")
            available[sector] = count
        self.assertEqual(
            available,
            {"residential": 347, "commercial": 347, "industrial": 324},
        )

    def test_customer_coverage_reconciles_for_all_sectors(self):
        for row in self.rows:
            for sector in SECTORS:
                eia_bundled = int(row[f"bundled_{sector}_customers"])
                pudl_bundled = int(row[f"pudl_bundled_{sector}_customers"])
                delivery = int(row[f"delivery_only_{sector}_customers"])
                total = int(row[f"total_distribution_{sector}_customers"])
                self.assertEqual(eia_bundled, pudl_bundled)
                self.assertEqual(total, pudl_bundled + delivery)
                share = row[f"bundled_{sector}_customer_share_pct"]
                if total:
                    self.assertAlmostEqual(
                        float(share), 100 * pudl_bundled / total, places=9
                    )
                else:
                    self.assertEqual(share, "")
                self.assertEqual(
                    row["coverage_source_status"],
                    "Derived from reported customer counts",
                )
                self.assertTrue(
                    row["coverage_source_url"].startswith(
                        "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/"
                    )
                )

    def test_industrial_missing_values_are_preserved_not_filled(self):
        missing = [
            row
            for row in self.rows
            if not row["industrial_average_price_cents_kwh"]
        ]
        self.assertEqual(len(missing), 36)
        self.assertEqual(
            Counter(int(row["utility_id_eia"]) for row in missing),
            {6369: 12, 66101: 11, 15748: 8, 3266: 2, 1179: 2, 6374: 1},
        )
        for row in missing:
            self.assertEqual(int(row["bundled_industrial_customers"]), 0)
            self.assertEqual(
                row["industrial_coverage_reconciliation"],
                "No EIA table row; PUDL reports zero bundled customers",
            )

    def test_minority_coverage_flags_are_explicit_and_do_not_change_prices(self):
        expected = {
            "residential": {
                "majority_coverage": 336,
                "minority_coverage": 11,
                "no_published_price": 13,
            },
            "commercial": {
                "majority_coverage": 312,
                "minority_coverage": 35,
                "no_published_price": 13,
            },
            "industrial": {
                "majority_coverage": 196,
                "minority_coverage": 128,
                "no_published_price": 36,
            },
        }
        for sector, expected_counts in expected.items():
            counts = Counter(row[f"{sector}_coverage_flag"] for row in self.rows)
            self.assertEqual(dict(counts), expected_counts)
            for row in self.rows:
                flag = row[f"{sector}_coverage_flag"]
                price = row[f"{sector}_average_price_cents_kwh"]
                if flag == "minority_coverage":
                    coverage = float(row[f"bundled_{sector}_customer_share_pct"])
                    self.assertTrue(price)
                    self.assertLess(coverage, 50)
                elif flag == "majority_coverage":
                    coverage = float(row[f"bundled_{sector}_customer_share_pct"])
                    self.assertTrue(price)
                    self.assertGreaterEqual(coverage, 50)
                else:
                    self.assertEqual(flag, "no_published_price")
                    self.assertFalse(price)
            self.assertIn("the price is not changed", self.rows[0]["coverage_flag_rule"])

    def test_known_residential_coverage_extremes_are_preserved(self):
        by_key = {
            (int(row["utility_id_eia"]), int(row["year"])): row for row in self.rows
        }
        self.assertLess(
            float(by_key[(3266, 2013)]["bundled_residential_customer_share_pct"]),
            0.01,
        )
        self.assertAlmostEqual(
            float(by_key[(54913, 2024)]["bundled_residential_customer_share_pct"]),
            29.420617,
            places=6,
        )
        self.assertEqual(
            float(by_key[(20038, 2024)]["bundled_residential_customer_share_pct"]),
            100.0,
        )

    def test_spot_checks_values_copied_from_eia_tables(self):
        by_key = {
            (int(row["utility_id_eia"]), int(row["year"])): row for row in self.rows
        }
        coned_2024 = by_key[(4226, 2024)]
        self.assertAlmostEqual(
            float(coned_2024["residential_average_price_cents_kwh"]),
            35.661640,
            places=6,
        )
        self.assertAlmostEqual(
            float(coned_2024["commercial_average_price_cents_kwh"]),
            28.196293,
            places=6,
        )
        self.assertAlmostEqual(
            float(coned_2024["industrial_average_price_cents_kwh"]),
            30.954324,
            places=6,
        )
        self.assertEqual(int(coned_2024["bundled_commercial_customers"]), 454400)
        self.assertEqual(int(coned_2024["bundled_industrial_customers"]), 6961)

    def test_site_data_files_match_processed_panel(self):
        self.assertEqual(PANEL_CSV.read_text(), SITE_CSV.read_text())
        json_records = json.loads(SITE_JSON.read_text())
        prefix = "window.NE_NY_PRICE_PANEL = "
        bundle = SITE_JS.read_text()
        self.assertTrue(bundle.startswith(prefix))
        self.assertTrue(bundle.endswith(";\n"))
        self.assertEqual(json_records, json.loads(bundle[len(prefix) : -2]))
        self.assertEqual(len(json_records), len(self.rows))


class TestPricePanelWebsite(unittest.TestCase):
    def test_navigation_separates_primary_pages_from_overview_sections(self):
        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        price = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        reliability = (
            PROJECT_ROOT / "site" / "reliability-panel-model.html"
        ).read_text()

        primary = overview.split(
            '<nav class="research-nav" aria-label="Primary navigation">',
            1,
        )[1].split("</nav>", 1)[0]
        self.assertEqual(primary.count("<a "), 4)
        self.assertIn(">Overview</a>", primary)
        self.assertIn(">Price model</a>", primary)
        self.assertIn(">Reliability model</a>", primary)
        self.assertIn(">Methods &amp; data</a>", primary)
        self.assertNotIn("Utility histories", primary)
        self.assertNotIn("ROE", primary)
        self.assertNotIn("Regional mix", primary)
        self.assertNotIn("Earlier analysis", primary)
        self.assertIn('class="overview-section-nav"', overview)

        price_nav = price.split(
            '<nav class="research-nav draft-model-nav"',
            1,
        )[1].split("</nav>", 1)[0]
        reliability_nav = reliability.split(
            '<nav class="research-nav draft-model-nav"',
            1,
        )[1].split("</nav>", 1)[0]
        self.assertEqual(price_nav.count("<a "), 3)
        self.assertEqual(reliability_nav.count("<a "), 3)
        self.assertIn("Earlier analysis archive", overview)

    def test_primary_visual_is_three_groups_of_two_by_five(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        script = (PROJECT_ROOT / "site" / "panel.js").read_text()
        self.assertIn('id="utility-matrix"', html)
        self.assertIn('class="matrix-scroll"', html)
        self.assertIn('const OWNERSHIP_ORDER = ["MTC", "DOM", "COOP"]', script)
        order_block = re.search(
            r"const UTILITY_ORDER = \[(.*?)\];", script, flags=re.DOTALL
        )
        self.assertIsNotNone(order_block)
        utility_ids = re.findall(r'"(?:MTC|DOM|COOP)_[^"]+"', order_block.group(1))
        self.assertEqual(len(utility_ids), 30)
        styles = (PROJECT_ROOT / "site" / "styles.css").read_text()
        self.assertIn("grid-template-columns: repeat(5, minmax(0, 1fr))", styles)
        self.assertIn("two rows of five", html)

    def test_selectors_contain_sector_price_and_reliability_measures(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        script = (PROJECT_ROOT / "site" / "panel.js").read_text()
        self.assertIn('id="customer-class"', html)
        for value in ("residential", "commercial", "industrial"):
            self.assertIn(f'value="{value}"', html)
        self.assertIn('id="panel-metric"', html)
        for value in ("price", "coverage", "saidi", "saifi", "caidi"):
            self.assertIn(f'value="{value}"', html)
        self.assertIn('id="reliability-scope"', html)
        self.assertIn('value="without-major-events"', html)
        self.assertIn('value="with-major-events"', html)
        self.assertIn("window.NE_NY_RELIABILITY_PANEL", script)
        self.assertIn('class: "mini-chart__method-line"', script)
        self.assertIn("previousYear = null", script)

    def test_dedicated_ownership_comparison_and_coverage_flags_are_visible(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        script = (PROJECT_ROOT / "site" / "panel.js").read_text()
        styles = (PROJECT_ROOT / "site" / "styles.css").read_text()
        self.assertIn('id="ownership-comparison"', html)
        self.assertIn('id="comparison-measure"', html)
        self.assertIn('id="comparison-customer-class"', html)
        self.assertIn('id="comparison-coverage-rule"', html)
        self.assertIn('id="comparison-price-basis"', html)
        self.assertIn('id="comparison-reliability-scope"', html)
        self.assertIn('value="all_published"', html)
        self.assertIn('value="majority_coverage"', html)
        self.assertIn('value="real_2024"', html)
        self.assertIn("Prices included", html)
        self.assertIn("Only prices covering at least 50% of customers", html)
        self.assertIn(
            "Do electricity prices differ across utility ownership types",
            html,
        )
        self.assertIn("window.NE_NY_OWNERSHIP_PRICE_SUMMARY", script)
        self.assertIn("ownership-comparison-chart__range", script)
        self.assertIn("ownership-comparison-chart__point--flagged", styles)
        self.assertIn("mini-chart__point--low-coverage", styles)
        self.assertIn("CPI_U_ANNUAL_2013_100", script)
        self.assertIn("reliabilitySummaryRecords", script)
        self.assertIn("Each line is a simple", html)
        self.assertIn("annual median", html)
        self.assertIn("Regional prices and selected reliability outcomes by ownership", html)
        self.assertIn("not represent every utility", html)
        self.assertIn("42-utility regional sample", html)
        self.assertIn("reviewed 30-utility sample", html)
        self.assertNotIn("Where fuel mix fits", html)

    def test_source_conflicted_reliability_values_are_withheld(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        script = (PROJECT_ROOT / "site" / "panel.js").read_text()
        self.assertIn("isReliabilityFieldExcluded", script)
        self.assertIn("published value", script)
        self.assertIn("conflicts", script)
        self.assertIn("withheld from the charts", html)
        self.assertRegex(html, r"full\s+2023 EIA\s+row")
        self.assertNotIn("1,061-minute 2017 value", html)

    def test_regional_generation_context_is_visible_and_sourced(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        script = (PROJECT_ROOT / "site" / "panel.js").read_text()
        styles = (PROJECT_ROOT / "site" / "styles.css").read_text()
        self.assertIn('id="regional-fuel-mix"', html)
        self.assertIn('src="data/iso_fuel_mix.js"', html)
        self.assertIn("EIA Form 923", html)
        self.assertIn("Imports are not included", html)
        self.assertIn("Fuel mix can help explain changes in regional supply costs", html)
        self.assertIn("setupIsoFuelMix", script)
        self.assertIn("iso-fuel-mix-chart__segment", script)
        self.assertIn(".iso-fuel-mix-charts", styles)

    def test_old_snapshot_and_single_utility_controls_are_removed(self):
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        for removed_id in (
            "price-snapshot",
            "panel-year",
            "panel-ownership",
            "panel-utility",
            "ownership-summary",
            "price-trend",
            "sample-table-body",
        ):
            self.assertNotIn(f'id="{removed_id}"', html)
        self.assertNotIn("Utilities included", html)


if __name__ == "__main__":
    unittest.main()
