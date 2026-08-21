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
        cls.results = reliability.build_results()
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

    def test_website_keeps_reliability_separate_from_price_causation(self) -> None:
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "panel.js").read_text()
        self.assertIn('id="reliability-model-finding"', html)
        self.assertIn("separate service-quality outcome, not a cause of prices", html)
        self.assertIn("data/ownership_reliability_model_results.js", html)
        self.assertIn("reliabilityModelFinding", javascript)
        self.assertIn(
            "window.NE_NY_OWNERSHIP_RELIABILITY_MODEL_RESULTS", javascript
        )


if __name__ == "__main__":
    unittest.main()
