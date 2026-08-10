import csv
import json
import statistics
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PANEL_FILE = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_2013_2024.csv"
SUMMARY_FILE = PROJECT_ROOT / "data" / "processed" / "ownership_price_summary_2013_2024.csv"
SITE_CSV = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.csv"
SITE_JSON = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.json"
SITE_JS = PROJECT_ROOT / "site" / "data" / "ownership_price_summary.js"
CUSTOMER_CLASSES = ("residential", "commercial", "industrial")
OWNERSHIP_TYPES = ("MTC", "DOM", "COOP")
COVERAGE_RULES = ("all_published", "majority_coverage")


class TestOwnershipPriceSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with PANEL_FILE.open(newline="") as source:
            cls.panel = list(csv.DictReader(source))
        with SUMMARY_FILE.open(newline="") as source:
            cls.summary = list(csv.DictReader(source))
        cls.by_key = {
            (
                row["customer_class"],
                row["coverage_rule"],
                int(row["year"]),
                row["ownership"],
            ): row
            for row in cls.summary
        }

    def test_complete_summary_grid(self):
        self.assertEqual(len(self.summary), 216)
        expected = {
            (customer_class, coverage_rule, year, ownership)
            for customer_class in CUSTOMER_CLASSES
            for coverage_rule in COVERAGE_RULES
            for year in range(2013, 2025)
            for ownership in OWNERSHIP_TYPES
        }
        self.assertEqual(set(self.by_key), expected)

    def test_all_medians_ranges_and_counts_reconcile_to_panel(self):
        for key, summary in self.by_key.items():
            customer_class, coverage_rule, year, ownership = key
            price_key = f"{customer_class}_average_price_cents_kwh"
            coverage_key = f"bundled_{customer_class}_customer_share_pct"
            published = [
                row
                for row in self.panel
                if int(row["year"]) == year
                and row["ownership"] == ownership
                and row[price_key]
            ]
            included = (
                published
                if coverage_rule == "all_published"
                else [row for row in published if float(row[coverage_key]) >= 50]
            )
            prices = [float(row[price_key]) for row in included]
            self.assertEqual(int(summary["published_price_count"]), len(published))
            self.assertEqual(int(summary["included_utility_count"]), len(included))
            self.assertEqual(
                int(summary["minority_coverage_count"]),
                sum(float(row[coverage_key]) < 50 for row in published),
            )
            if prices:
                self.assertAlmostEqual(
                    float(summary["median_price_cents_kwh"]),
                    statistics.median(prices),
                    places=9,
                )
                self.assertEqual(float(summary["minimum_price_cents_kwh"]), min(prices))
                self.assertEqual(float(summary["maximum_price_cents_kwh"]), max(prices))
            else:
                self.assertEqual(summary["median_price_cents_kwh"], "")
                self.assertEqual(summary["minimum_price_cents_kwh"], "")
                self.assertEqual(summary["maximum_price_cents_kwh"], "")

    def test_ownership_is_assigned_in_each_year_not_fixed_at_2024(self):
        self.assertEqual(
            int(self.by_key[("residential", "all_published", 2013, "MTC")]["included_utility_count"]),
            9,
        )
        self.assertEqual(
            int(self.by_key[("residential", "all_published", 2017, "MTC")]["included_utility_count"]),
            11,
        )
        self.assertEqual(
            int(self.by_key[("residential", "all_published", 2017, "DOM")]["included_utility_count"]),
            8,
        )

    def test_known_2024_selected_sample_medians(self):
        expected = {"MTC": 23.150955, "DOM": 28.3850455, "COOP": 17.5244515}
        for ownership, value in expected.items():
            row = self.by_key[("residential", "all_published", 2024, ownership)]
            self.assertAlmostEqual(float(row["median_price_cents_kwh"]), value, places=6)

    def test_majority_coverage_sensitivity_applies_rule_transparently(self):
        row = self.by_key[("industrial", "majority_coverage", 2013, "DOM")]
        self.assertEqual(int(row["published_price_count"]), 8)
        self.assertEqual(int(row["included_utility_count"]), 2)
        self.assertEqual(int(row["excluded_minority_coverage_count"]), 6)
        self.assertAlmostEqual(float(row["median_price_cents_kwh"]), 17.5281358)

    def test_site_data_files_match_processed_summary(self):
        self.assertEqual(SUMMARY_FILE.read_text(), SITE_CSV.read_text())
        records = json.loads(SITE_JSON.read_text())
        prefix = "window.NE_NY_OWNERSHIP_PRICE_SUMMARY = "
        bundle = SITE_JS.read_text()
        self.assertTrue(bundle.startswith(prefix))
        self.assertTrue(bundle.endswith(";\n"))
        self.assertEqual(records, json.loads(bundle[len(prefix) : -2]))
        self.assertEqual(len(records), 216)


if __name__ == "__main__":
    unittest.main()
