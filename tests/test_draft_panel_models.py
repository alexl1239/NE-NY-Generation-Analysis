"""Regression and reproducibility checks for the draft panel-model page."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import build_draft_panel_models as draft  # noqa: E402


EXPECTED_COMMON_SAMPLES = {
    "residential": (287, 26),
    "commercial": (287, 26),
    "industrial": (277, 26),
}

EXPECTED_BASELINE_OWNERSHIP = {
    "residential": {"MTC": -4.949682, "COOP": -9.310098},
    "commercial": {"MTC": -5.380471, "COOP": -6.776008},
    "industrial": {"MTC": -3.790527, "COOP": -6.680256},
}


class DraftPanelModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = draft.build_analysis_table()
        cls.results = draft.build_results(cls.analysis)
        cls.price_models = {
            (model["customer_class"], model["specification"]): model
            for model in cls.results["price_models"]
        }

    def test_student_t_p_value_matches_known_critical_values(self) -> None:
        self.assertAlmostEqual(draft.student_t_two_sided_p_value(1.0, 1), 0.5, places=12)
        self.assertAlmostEqual(
            draft.student_t_two_sided_p_value(2.045230, 29),
            0.05,
            places=6,
        )
        self.assertAlmostEqual(
            draft.student_t_two_sided_p_value(2.063899, 24),
            0.05,
            places=6,
        )

    def test_analysis_table_preserves_reviewed_panel(self) -> None:
        self.assertEqual(len(self.analysis), 360)
        self.assertEqual(self.analysis["panel_id"].nunique(), 30)
        self.assertEqual(set(self.analysis["iso_market"]), {"ISO-NE", "NYISO"})
        self.assertTrue(
            (self.analysis.loc[self.analysis["state"] == "NY", "iso_market"] == "NYISO").all()
        )
        self.assertTrue(
            (self.analysis.loc[self.analysis["state"] != "NY", "iso_market"] == "ISO-NE").all()
        )

    def test_primary_models_use_the_same_complete_case_rows(self) -> None:
        for customer_class, expected_counts in EXPECTED_COMMON_SAMPLES.items():
            counts = {
                (
                    model["observation_count"],
                    model["utility_cluster_count"],
                )
                for (model_class, _), model in self.price_models.items()
                if model_class == customer_class
            }
            self.assertEqual(counts, {expected_counts})

    def test_primary_designs_are_full_rank_and_keep_reliability_separate(self) -> None:
        for model in self.results["price_models"]:
            self.assertEqual(model["design_rank"], model["parameter_count"])
            terms = {row["term"] for row in model["coefficients"]}
            has_saidi = "routine_saidi_per_100_minutes" in terms
            has_caidi = "routine_caidi_per_10_minutes" in terms
            self.assertFalse(has_saidi and has_caidi)
            self.assertTrue(all(0 <= row["p_value"] <= 1 for row in model["coefficients"]))

    def test_baseline_ownership_estimates_match_reviewed_values(self) -> None:
        for customer_class, expected in EXPECTED_BASELINE_OWNERSHIP.items():
            model = self.price_models[(customer_class, "baseline")]
            coefficients = {
                row["term"]: row for row in model["coefficients"]
            }
            for ownership, estimate in expected.items():
                self.assertAlmostEqual(
                    coefficients[f"ownership_{ownership}"]["estimate"],
                    estimate,
                    places=5,
                )

    def test_reliability_additions_do_not_explain_the_price_gap_in_draft(self) -> None:
        diagnostics = self.results["diagnostics"]["ownership_coefficient_changes"]
        for customer_class in draft.CUSTOMER_CLASSES:
            for ownership in draft.OWNERSHIP_TERMS:
                change = diagnostics[customer_class][ownership]
                self.assertLess(abs(change["saidi_change_from_baseline"]), 0.5)
                self.assertLess(abs(change["caidi_change_from_baseline"]), 0.5)

        for model in self.results["price_models"]:
            if model["specification"] in {"saidi", "caidi"}:
                term = (
                    "routine_saidi_per_100_minutes"
                    if model["specification"] == "saidi"
                    else "routine_caidi_per_10_minutes"
                )
                result = next(row for row in model["coefficients"] if row["term"] == term)
                self.assertGreater(result["p_value"], 0.05)

    def test_state_and_expanded_checks_are_stored_as_secondary_results(self) -> None:
        checks = self.results["decision_checks"]
        self.assertEqual(len(checks["state_control_models"]), 9)
        self.assertEqual(len(checks["state_control_reliability_outcome_models"]), 2)
        self.assertEqual(len(checks["expanded_price_models"]), 3)
        expanded_counts = {
            model["customer_class"]: model["utility_cluster_count"]
            for model in checks["expanded_price_models"]
        }
        self.assertEqual(expanded_counts, {"residential": 42, "commercial": 42, "industrial": 41})

    def test_written_site_copies_match_processed_outputs(self) -> None:
        processed = json.loads(draft.PROCESSED_RESULTS_OUTPUT.read_text())
        site = json.loads(draft.SITE_RESULTS_OUTPUT.read_text())
        self.assertEqual(processed, site)
        self.assertEqual(
            draft.PROCESSED_ANALYSIS_OUTPUT.read_text(),
            draft.SITE_ANALYSIS_OUTPUT.read_text(),
        )
        javascript = draft.SITE_RESULTS_JS_OUTPUT.read_text().strip()
        prefix = "window.NE_NY_DRAFT_PANEL_MODEL_RESULTS = "
        self.assertTrue(javascript.startswith(prefix))
        self.assertTrue(javascript.endswith(";"))
        self.assertEqual(json.loads(javascript[len(prefix) : -1]), processed)

    def test_draft_page_is_separate_linked_and_plainly_labeled(self) -> None:
        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        page = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "draft-panel-model.js").read_text()
        self.assertIn('href="draft-panel-model.html"', overview)
        self.assertIn("Draft—not final and not causal", page)
        self.assertIn('id="draft-customer-class"', page)
        self.assertIn('id="draft-reliability-metric"', page)
        self.assertIn("data/draft_panel_model_results.js", page)
        self.assertIn("The share of price variation tracked by the whole model", page)
        self.assertIn("renderDecisionChecks", javascript)
        self.assertNotIn("<svg", page)


if __name__ == "__main__":
    unittest.main()
