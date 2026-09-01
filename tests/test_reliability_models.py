"""Checks for the simple ownership-reliability models."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import build_reliability_models as reliability  # noqa: E402


EXPECTED_PRIMARY_COUNTS = {
    "saidi": (293, 26),
    "saifi": (293, 27),
    "caidi": (289, 26),
}


class ReliabilityModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = reliability.pd.read_csv(reliability.INPUT)
        cls.results = reliability.build_results()
        cls.focused = reliability.build_focused_results(cls.audit, cls.results)
        cls.analysis = reliability.build_analysis_table(cls.audit)
        cls.models = {
            (model["metric"], model["event_scope"], model["reporting_sample"]): model
            for model in cls.results["models"]
        }

    def test_expected_structure(self) -> None:
        self.assertEqual(len(self.models), 12)
        self.assertEqual(self.results["reference_ownership"], "DOM")
        self.assertIn("reporting-method", self.results["model"])
        self.assertIn("not causal", self.results["interpretation_limit"])

    def test_primary_models_apply_reviewed_exclusions(self) -> None:
        for metric, counts in EXPECTED_PRIMARY_COUNTS.items():
            model = self.models[(metric, "without_major_events", "all_methods")]
            self.assertEqual(
                (model["observation_count"], model["utility_cluster_count"]), counts
            )
            self.assertEqual(model["design_rank"], model["parameter_count"])

    def test_primary_models_find_no_clear_ownership_difference(self) -> None:
        for metric in reliability.METRICS:
            model = self.models[(metric, "without_major_events", "all_methods")]
            self.assertTrue(
                all(
                    not row["confidence_interval_excludes_zero"]
                    for row in model["ownership_results"]
                )
            )

    def test_primary_saidi_p_values_are_exact_and_uncertain(self) -> None:
        model = self.models[("saidi", "without_major_events", "all_methods")]
        rows = {row["ownership"]: row for row in model["ownership_results"]}
        self.assertAlmostEqual(rows["MTC"]["p_value"], 0.1086391215, places=9)
        self.assertAlmostEqual(rows["COOP"]["p_value"], 0.3511323374, places=9)
        self.assertTrue(all(0 <= row["p_value"] <= 1 for row in rows.values()))

    def test_sensitivity_results_are_not_misrepresented_as_stable(self) -> None:
        primary_significance = []
        sensitivity_significance = []
        for model in self.results["models"]:
            flags = [
                row["confidence_interval_excludes_zero"]
                for row in model["ownership_results"]
            ]
            if (
                model["event_scope"] == "without_major_events"
                and model["reporting_sample"] == "all_methods"
            ):
                primary_significance.extend(flags)
            else:
                sensitivity_significance.extend(flags)
        self.assertFalse(any(primary_significance))
        self.assertTrue(any(sensitivity_significance))

    def test_written_site_copy_matches_processed_copy(self) -> None:
        processed = json.loads(reliability.PROCESSED_OUTPUT.read_text())
        site = json.loads(reliability.SITE_JSON_OUTPUT.read_text())
        self.assertEqual(processed, site)
        text = reliability.SITE_JS_OUTPUT.read_text().strip()
        prefix = "window.NE_NY_OWNERSHIP_RELIABILITY_MODEL_RESULTS = "
        self.assertTrue(text.startswith(prefix))
        self.assertEqual(json.loads(text[len(prefix) : -1]), processed)

        focused_processed = json.loads(reliability.FOCUSED_PROCESSED_OUTPUT.read_text())
        focused_site = json.loads(reliability.FOCUSED_SITE_JSON_OUTPUT.read_text())
        self.assertEqual(focused_processed, focused_site)
        self.assertEqual(focused_processed, self.focused)
        focused_text = reliability.FOCUSED_SITE_JS_OUTPUT.read_text().strip()
        focused_prefix = "window.NE_NY_RELIABILITY_PANEL_MODEL_RESULTS = "
        self.assertTrue(focused_text.startswith(focused_prefix))
        self.assertEqual(
            json.loads(focused_text[len(focused_prefix) : -1]),
            focused_processed,
        )
        self.assertEqual(
            reliability.ANALYSIS_PROCESSED_OUTPUT.read_text(),
            reliability.ANALYSIS_SITE_OUTPUT.read_text(),
        )

    def test_focused_page_uses_one_saidi_model_and_complete_audit_table(self) -> None:
        self.assertEqual(self.focused["primary_model"]["metric"], "saidi")
        self.assertEqual(
            (
                self.focused["sample"]["included_utility_years"],
                self.focused["sample"]["included_utilities"],
            ),
            (293, 26),
        )
        self.assertEqual(len(self.analysis), 360)
        self.assertEqual(int(self.analysis["included_primary_model"].sum()), 293)
        self.assertEqual(self.analysis["panel_id"].nunique(), 30)

        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        price_page = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        page = (PROJECT_ROOT / "site" / "reliability-panel-model.html").read_text()
        javascript = (
            PROJECT_ROOT / "site" / "reliability-panel-model.js"
        ).read_text()
        self.assertIn('href="reliability-panel-model.html"', overview)
        self.assertIn('href="reliability-panel-model.html"', price_page)
        self.assertIn("Ownership and routine outage duration", page)
        self.assertIn('id="reliability-results-table"', page)
        self.assertIn('id="reliability-trend-chart"', page)
        self.assertIn('id="reliability-data-body"', page)
        self.assertIn("Weather is not included", page)
        self.assertNotIn("SAIFI", page)
        self.assertNotIn("CAIDI", page)
        self.assertIn("renderTrend", javascript)
        self.assertIn("renderResults", javascript)
        self.assertIn("renderAnalysisData", javascript)
        self.assertIn("Inconclusive: CI includes 0", javascript)
        self.assertNotIn("professor", page.lower())

    def test_price_page_limits_reliability_to_an_exploratory_saidi_check(self) -> None:
        html = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "draft-panel-model.js").read_text()
        self.assertIn('id="saidi-comparison-groups"', html)
        self.assertIn("Exploratory SAIDI check", html)
        self.assertIn("not causal effects", html)
        self.assertIn("renderSaidiComparison", javascript)
        self.assertNotIn("renderReliabilityResults", javascript)
        self.assertNotIn("reliability_outcome_models", javascript)
        self.assertNotIn('id="draft-reliability-cards"', html)


if __name__ == "__main__":
    unittest.main()
