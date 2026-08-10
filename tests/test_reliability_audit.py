import csv
import json
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_coverage_audit_2013_2024.csv"
)
VALIDATION_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliability_source_validation_2013_2024.csv"
)
INDEPENDENT_CHECKS_CSV = (
    PROJECT_ROOT / "data" / "manual" / "reliability_independent_checks.csv"
)
SITE_CSV = PROJECT_ROOT / "site" / "data" / "reliability_panel.csv"
SITE_JSON = PROJECT_ROOT / "site" / "data" / "reliability_panel.json"
SITE_JS = PROJECT_ROOT / "site" / "data" / "reliability_panel.js"


class TestReliabilityCoverageAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with AUDIT_CSV.open(newline="") as source:
            cls.rows = list(csv.DictReader(source))
        cls.by_key = {
            (int(row["utility_id_eia"]), int(row["year"])): row
            for row in cls.rows
        }

    def test_audit_has_one_row_per_selected_utility_year(self):
        self.assertEqual(len(self.rows), 360)
        self.assertEqual(len({row["panel_id"] for row in self.rows}), 30)
        self.assertEqual({int(row["year"]) for row in self.rows}, set(range(2013, 2025)))
        self.assertEqual(
            set(Counter(row["panel_id"] for row in self.rows).values()),
            {12},
        )
        self.assertEqual(
            len({(row["panel_id"], row["year"]) for row in self.rows}),
            360,
        )

    def test_missing_source_rows_are_preserved(self):
        missing = [
            (int(row["utility_id_eia"]), int(row["year"]))
            for row in self.rows
            if row["reliability_row_status"] == "not_reported"
        ]
        self.assertEqual(
            Counter(utility_id for utility_id, _ in missing),
            {14605: 12, 6369: 12, 66101: 11, 18488: 3, 3249: 1},
        )
        self.assertEqual(
            Counter(row["reliability_row_status"] for row in self.rows),
            {"reported": 321, "not_reported": 39},
        )

    def test_missing_metric_counts_are_preserved(self):
        expected_non_missing = {
            "saidi_w_major_event_days_minutes": 305,
            "saidi_wo_major_event_days_minutes": 294,
            "saifi_w_major_event_days_customers": 318,
            "saifi_wo_major_event_days_customers": 295,
            "caidi_w_major_event_days_minutes": 305,
            "caidi_wo_major_event_days_minutes": 291,
        }
        for field, expected in expected_non_missing.items():
            self.assertEqual(
                sum(row[field] != "" for row in self.rows),
                expected,
                field,
            )

    def test_incomplete_reported_rows_are_flagged(self):
        incomplete = {
            (int(row["utility_id_eia"]), int(row["year"]))
            for row in self.rows
            if row["reliability_row_status"] == "reported"
            and row["display_metrics_complete"] == "False"
        }
        self.assertEqual(len(incomplete), 32)
        self.assertEqual(
            Counter(utility_id for utility_id, _ in incomplete),
            {2548: 12, 3477: 12, 15748: 5, 19791: 2, 20038: 1},
        )

    def test_reporting_standard_changes_are_not_hidden(self):
        changed_ids = {
            int(row["utility_id_eia"])
            for row in self.rows
            if row["standard_changed_during_panel"] == "True"
        }
        self.assertEqual(changed_ids, {3249, 5930, 11804, 13511, 19497, 24590})
        self.assertEqual(self.by_key[(5930, 2016)]["reporting_standard"], "other_standard")
        self.assertEqual(self.by_key[(5930, 2017)]["reporting_standard"], "ieee_standard")
        self.assertEqual(self.by_key[(11804, 2020)]["reporting_standard"], "other_standard")
        self.assertEqual(self.by_key[(11804, 2021)]["reporting_standard"], "ieee_standard")

    def test_non_ieee_rows_are_retained_but_limited_to_descriptive_use(self):
        consistent_non_ieee = [
            row
            for row in self.rows
            if row["comparability_status"] == "consistent_other_standard"
            and row["reliability_row_status"] == "reported"
        ]
        self.assertEqual(len(consistent_non_ieee), 84)
        self.assertEqual(
            {row["analysis_use"] for row in consistent_non_ieee},
            {
                "descriptive_only_non_ieee_method",
                "descriptive_only_incomplete_metrics",
            },
        )
        self.assertTrue(
            all(row["official_eia_validation_status"] == "exact_match" for row in consistent_non_ieee)
        )

    def test_pudl_caidi_matches_saidi_divided_by_saifi(self):
        variants = (
            (
                "saidi_w_major_event_days_minutes",
                "saifi_w_major_event_days_customers",
                "caidi_w_major_event_days_minutes",
            ),
            (
                "saidi_wo_major_event_days_minutes",
                "saifi_wo_major_event_days_customers",
                "caidi_wo_major_event_days_minutes",
            ),
        )
        for row in self.rows:
            for saidi_field, saifi_field, caidi_field in variants:
                if not all(row[field] for field in (saidi_field, saifi_field, caidi_field)):
                    continue
                saidi = float(row[saidi_field])
                saifi = float(row[saifi_field])
                caidi = float(row[caidi_field])
                self.assertAlmostEqual(caidi, saidi / saifi, places=4)

    def test_every_row_has_traceable_sources(self):
        for row in self.rows:
            self.assertTrue(row["eia_source_page"].startswith("https://www.eia.gov/"))
            self.assertTrue(row["eia_source_file_url"].startswith("https://www.eia.gov/"))
            self.assertTrue(
                row["pudl_source_url"].startswith(
                    "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/"
                )
            )
            self.assertEqual(
                row["source_report"],
                "EIA Form 861, Annual Electric Power Industry Report",
            )
            self.assertEqual(row["retrieved_date"], "2026-08-08")

    def test_direct_eia_source_validation_has_no_mismatches(self):
        with VALIDATION_CSV.open(newline="") as source:
            validation = list(csv.DictReader(source))
        self.assertEqual(len(validation), 360)
        self.assertEqual(
            {int(row["year"]) for row in validation},
            set(range(2013, 2025)),
        )
        self.assertEqual(sum(int(row["fields_compared"]) for row in validation), 2841)
        self.assertEqual({row["mismatch_count"] for row in validation}, {"0"})
        self.assertEqual(
            Counter(row["validation_status"] for row in validation),
            {"exact_match": 321, "matching_absence": 39},
        )
        for row in validation:
            self.assertEqual(
                row["eia_reporting_standard"],
                row["pudl_reporting_standard"],
            )
            self.assertTrue(row["eia_source_file_url"].startswith("https://www.eia.gov/"))

    def test_reliability_values_have_no_impossible_ordering(self):
        metric_pairs = (
            (
                "saidi_w_major_event_days_minutes",
                "saidi_wo_major_event_days_minutes",
            ),
            (
                "saifi_w_major_event_days_customers",
                "saifi_wo_major_event_days_customers",
            ),
        )
        loss_pairs = (
            (
                "saidi_w_major_event_days_minutes",
                "saidi_w_major_event_days_minus_loss_of_service_minutes",
            ),
            (
                "saifi_w_major_event_days_customers",
                "saifi_w_major_event_days_minus_loss_of_service_customers",
            ),
        )
        for row in self.rows:
            for field in (
                "saidi_w_major_event_days_minutes",
                "saidi_wo_major_event_days_minutes",
                "saifi_w_major_event_days_customers",
                "saifi_wo_major_event_days_customers",
                "caidi_w_major_event_days_minutes",
                "caidi_wo_major_event_days_minutes",
            ):
                if row[field]:
                    self.assertGreaterEqual(float(row[field]), 0)
            for included_field, excluded_field in metric_pairs:
                if row[included_field] and row[excluded_field]:
                    self.assertGreaterEqual(
                        float(row[included_field]),
                        float(row[excluded_field]),
                    )
            for all_field, loss_removed_field in loss_pairs:
                if row[all_field] and row[loss_removed_field]:
                    self.assertLessEqual(
                        float(row[loss_removed_field]),
                        float(row[all_field]),
                    )

    def test_nstar_2017_raw_value_is_preserved_but_withheld_from_analysis(self):
        nstar = self.by_key[(54913, 2017)]
        self.assertEqual(int(float(nstar["reliability_customers"])), 1_197_922)
        self.assertAlmostEqual(
            float(nstar["saifi_wo_major_event_days_customers"]),
            0.070,
            places=3,
        )
        self.assertAlmostEqual(
            float(nstar["caidi_wo_major_event_days_minutes"]),
            1061.4286,
            places=4,
        )
        self.assertEqual(
            nstar["analysis_excluded_fields"],
            "saifi_wo_major_event_days_customers|caidi_wo_major_event_days_minutes",
        )
        self.assertEqual(
            nstar["review_status"],
            "source_conflict_withheld_from_analysis",
        )
        self.assertIn(
            "/dockets/docket/5574",
            nstar["independent_crosscheck_source_url"],
        )
        self.assertIn("neither supports EIA's 0.070", nstar["independent_crosscheck_note"])
        other_values = [
            float(row["caidi_wo_major_event_days_minutes"])
            for row in self.rows
            if row["caidi_wo_major_event_days_minutes"]
            and not (
                int(row["utility_id_eia"]) == 54913 and int(row["year"]) == 2017
            )
        ]
        self.assertLess(max(other_values), 300)

    def test_nstar_2023_duplicated_eia_row_is_withheld(self):
        nstar = self.by_key[(54913, 2023)]
        clp = self.by_key[(4176, 2023)]
        duplicated_fields = (
            "reliability_customers",
            "saidi_w_major_event_days_minutes",
            "saidi_wo_major_event_days_minutes",
            "saifi_w_major_event_days_customers",
            "saifi_wo_major_event_days_customers",
            "caidi_w_major_event_days_minutes",
            "caidi_wo_major_event_days_minutes",
        )
        for field in duplicated_fields:
            self.assertEqual(nstar[field], clp[field], field)
        exclusions = set(nstar["analysis_excluded_fields"].split("|"))
        self.assertTrue(set(duplicated_fields).issubset(exclusions))
        self.assertEqual(
            nstar["independent_crosscheck_status"],
            "eia_row_conflicts_with_regulator_filing",
        )
        self.assertAlmostEqual(
            float(nstar["independent_crosscheck_saidi"]),
            48.021,
            places=3,
        )
        self.assertAlmostEqual(
            float(nstar["independent_crosscheck_saifi"]),
            0.662,
            places=3,
        )
        self.assertAlmostEqual(
            float(nstar["independent_crosscheck_caidi"]),
            72.534,
            places=3,
        )
        self.assertEqual(
            int(float(nstar["independent_crosscheck_customer_count"])),
            1_468_015,
        )
        self.assertIn("1,468,015", nstar["independent_crosscheck_note"])

    def test_independent_check_register_is_traceable(self):
        with INDEPENDENT_CHECKS_CSV.open(newline="") as source:
            checks = list(csv.DictReader(source))
        self.assertEqual(len(checks), 7)
        self.assertEqual(
            Counter(int(row["utility_id_eia"]) for row in checks),
            {4176: 5, 54913: 2},
        )
        self.assertTrue(all(row["source_url"].startswith("https://") for row in checks))

    def test_site_reliability_files_match_the_processed_audit(self):
        self.assertEqual(AUDIT_CSV.read_text(), SITE_CSV.read_text())
        json_records = json.loads(SITE_JSON.read_text())
        prefix = "window.NE_NY_RELIABILITY_PANEL = "
        bundle = SITE_JS.read_text()
        self.assertTrue(bundle.startswith(prefix))
        self.assertTrue(bundle.endswith(";\n"))
        self.assertEqual(json_records, json.loads(bundle[len(prefix) : -2]))
        self.assertEqual(len(json_records), 360)
        by_key = {
            (int(row["utility_id_eia"]), int(row["year"])): row
            for row in json_records
        }
        self.assertIsNone(
            by_key[(18488, 2013)]["saidi_wo_major_event_days_minutes"]
        )


if __name__ == "__main__":
    unittest.main()
