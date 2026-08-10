import csv
import json
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "iso_fuel_mix_2013_2024.csv"
CROSSCHECK_CSV = (
    PROJECT_ROOT / "data" / "processed" / "iso_fuel_mix_crosschecks_2024.csv"
)
SITE_CSV = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.csv"
SITE_JSON = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.json"
SITE_JS = PROJECT_ROOT / "site" / "data" / "iso_fuel_mix.js"


class TestIsoFuelMix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with PROCESSED_CSV.open(newline="") as source:
            cls.rows = list(csv.DictReader(source))

    def test_complete_two_region_panel(self):
        self.assertEqual(len(self.rows), 192)
        self.assertEqual({row["region"] for row in self.rows}, {"NYISO", "ISO-NE"})
        self.assertEqual({int(row["year"]) for row in self.rows}, set(range(2013, 2025)))
        self.assertEqual(
            set(Counter((row["region"], row["year"]) for row in self.rows).values()),
            {8},
        )

    def test_shares_reconcile_and_values_are_nonnegative(self):
        groups = {}
        for row in self.rows:
            key = (row["region"], int(row["year"]))
            groups.setdefault(key, []).append(row)
            self.assertGreaterEqual(float(row["net_generation_mwh"]), 0)
            self.assertLessEqual(float(row["excluded_nonpositive_generation_mwh"]), 0)
            self.assertTrue(row["eia_source_url"].startswith("https://www.eia.gov/"))
            self.assertIn("regional generation", row["definition_note"])
        for rows in groups.values():
            self.assertAlmostEqual(sum(float(row["share_pct"]) for row in rows), 100, places=4)
            total = float(rows[0]["positive_generation_total_mwh"])
            self.assertAlmostEqual(
                sum(float(row["net_generation_mwh"]) for row in rows),
                total,
                places=2,
            )
            excluded = abs(float(rows[0]["excluded_nonpositive_generation_mwh"]))
            self.assertLess(excluded / total, 0.0002)

    def test_2024_totals_are_checked_against_iso_reports(self):
        with CROSSCHECK_CSV.open(newline="") as source:
            checks = list(csv.DictReader(source))
        self.assertEqual(len(checks), 2)
        self.assertEqual({row["region"] for row in checks}, {"NYISO", "ISO-NE"})
        for row in checks:
            self.assertEqual(row["year"], "2024")
            self.assertTrue(row["source_url"].startswith("https://"))
            self.assertLess(abs(float(row["difference_pct_of_iso_total"])), 3.1)

    def test_site_data_matches_processed_data(self):
        with SITE_CSV.open(newline="") as source:
            site_csv_rows = list(csv.DictReader(source))
        self.assertEqual(site_csv_rows, self.rows)
        site_json_rows = json.loads(SITE_JSON.read_text())
        normalized_json = [{key: str(value) for key, value in row.items()} for row in site_json_rows]
        normalized_csv = [
            {
                key: (
                    str(float(value))
                    if key
                    in {
                        "net_generation_mwh",
                        "share_pct",
                        "positive_generation_total_mwh",
                        "excluded_nonpositive_generation_mwh",
                    }
                    else value
                )
                for key, value in row.items()
            }
            for row in self.rows
        ]
        self.assertEqual(normalized_json, normalized_csv)
        self.assertTrue(SITE_JS.read_text().startswith("window.NE_NY_ISO_FUEL_MIX = ["))


if __name__ == "__main__":
    unittest.main()
